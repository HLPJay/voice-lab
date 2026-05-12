# P6-E：批量执行并发化

## 背景

当前 `batch_orchestration_service.py` 的 `execute()` 方法是串行执行：

```python
for segment in segments:
    segment = await self._process_segment(session, segment, ...)
```

10 段 × 3-5 秒/段 = 30-50 秒。改为受控并发后可缩短到接近单段耗时。

## 目标

将串行 for 循环改为 `asyncio.Semaphore` + `asyncio.gather` 并发执行，同时保证：
1. 并发度可控（不超配 Provider API 限额）
2. 合并时段序不变
3. SQLite 写入不冲突
4. 进度实时更新
5. 现有测试全部通过

## 涉及文件

| 文件 | 操作 |
|------|------|
| `app/core/config.py` | 新增配置项 |
| `app/services/batch_orchestration_service.py` | 修改 `execute()` 方法 |
| `tests/test_batch_orchestration.py` | 新增并发测试 |

## 实施细节

### 1. `app/core/config.py` — 新增配置项

在 Settings 类中添加：

```python
batch_max_concurrency: int = 5
```

位置：放在 `clone_audio_max_size_mb` 下方。

### 2. `app/services/batch_orchestration_service.py` — 修改 `execute()`

#### 2.1 核心思路

- 用 `asyncio.Semaphore(settings.batch_max_concurrency)` 控制并发上限
- 每个段在独立的 `_process_segment_isolated()` 中获取**独立 Session**，处理完立即关闭
- 用 `asyncio.gather(*tasks, return_exceptions=True)` 并发执行所有 pending 段
- gather 结果按 segment.index 原始顺序排列（因为 tasks 列表已按 index 排序）
- gather 完成后，用**主 Session** 统一读取最新状态、执行合并、更新 batch_job

#### 2.2 需要新增的方法

```python
async def _process_segment_isolated(
    self,
    semaphore: asyncio.Semaphore,
    segment_id: str,
    provider: str,
    output_format: str,
    config: dict,
) -> tuple[str, str, str | None]:
    """在独立 Session 中处理单个 segment，返回 (segment_id, status, error_message)。"""
    async with semaphore:
        from app.core.database import get_engine
        session = Session(get_engine())
        try:
            segment = session.get(BatchSegment, segment_id)
            if not segment:
                return (segment_id, BatchStatus.failed, "Segment not found")

            segment = await self._process_segment(
                session, segment, provider, output_format, config
            )
            session.commit()
            return (segment_id, segment.status, None)
        except Exception as exc:
            self.logger.error(
                "segment_failed segment_id=%s error=%s", segment_id, str(exc)
            )
            # 在独立 session 中标记失败
            try:
                segment = session.get(BatchSegment, segment_id)
                if segment:
                    segment.status = BatchStatus.failed
                    segment.error_message = str(exc)[:500]
                    segment.updated_at = utc_now_iso()
                    session.add(segment)
                    session.commit()
            except Exception:
                pass
            return (segment_id, BatchStatus.failed, str(exc)[:500])
        finally:
            session.close()
```

#### 2.3 修改 `execute()` 方法

将现有的 `for segment in segments:` 循环替换为：

```python
async def execute(self, session: Session, batch_job_id: str) -> None:
    """执行批量任务：并发生成 → 合并 → 更新状态。"""
    batch_job = session.get(BatchJob, batch_job_id)
    if not batch_job:
        self.logger.error("batch_execute batch_job_id=%s not found", batch_job_id)
        return

    batch_job.status = BatchStatus.running
    batch_job.updated_at = utc_now_iso()
    session.add(batch_job)
    session.commit()

    segments = list(session.exec(
        select(BatchSegment).where(
            BatchSegment.batch_job_id == batch_job_id
        ).order_by(BatchSegment.index)
    ).all())

    config = {}
    try:
        config = json.loads(batch_job.config_json or "{}")
    except json.JSONDecodeError:
        pass

    settings = get_settings()
    provider = batch_job.provider or settings.voice_provider
    output_format = batch_job.output_format or "mp3"
    silence_ms = batch_job.silence_between_ms or 300

    # ---- 并发执行 pending 段 ----
    semaphore = asyncio.Semaphore(settings.batch_max_concurrency)
    pending_tasks = []

    for segment in segments:
        if segment.status == BatchStatus.success:
            continue  # 跳过已成功的段（retry 场景）
        pending_tasks.append(
            self._process_segment_isolated(
                semaphore, segment.id, provider, output_format, config
            )
        )

    if pending_tasks:
        await asyncio.gather(*pending_tasks)

    # ---- 并发执行完毕，刷新状态 ----
    # 重新加载所有 segment（因为并发中用了独立 session 修改）
    session.expire_all()
    segments = list(session.exec(
        select(BatchSegment).where(
            BatchSegment.batch_job_id == batch_job_id
        ).order_by(BatchSegment.index)
    ).all())

    # 收集成功段的音频路径（按 index 顺序 — 保证合并顺序正确）
    success_audio_paths = []
    success_timelines = []
    success_durations = []

    for segment in segments:
        if segment.status == BatchStatus.success and segment.audio_asset_id:
            audio_asset = session.get(AudioAsset, segment.audio_asset_id)
            if audio_asset:
                success_audio_paths.append(audio_asset.file_path)
                subtitle_asset = session.exec(
                    select(SubtitleAsset).where(
                        SubtitleAsset.audio_asset_id == segment.audio_asset_id
                    ).limit(1)
                ).one_or_none()
                timeline = json.loads(subtitle_asset.timeline_json) if subtitle_asset else []
                success_timelines.append(timeline)
                success_durations.append(segment.duration_ms or 0)

    # ---- 更新进度 ----
    batch_job = session.get(BatchJob, batch_job_id)
    batch_job.completed_segments = sum(1 for s in segments if s.status == BatchStatus.success)
    batch_job.failed_segments = sum(1 for s in segments if s.status == BatchStatus.failed)
    batch_job.updated_at = utc_now_iso()
    session.add(batch_job)
    session.commit()

    # ---- 合并（与原逻辑完全一致，不改动） ----
    # ... 保持现有 merge 逻辑不变 ...

    # ---- 最终状态 ----
    failed_count = sum(1 for s in segments if s.status == BatchStatus.failed)
    if failed_count == len(segments):
        batch_job.status = BatchStatus.failed
    elif failed_count > 0:
        batch_job.status = BatchStatus.partial
    else:
        batch_job.status = BatchStatus.success

    batch_job.updated_at = utc_now_iso()
    session.add(batch_job)
    session.commit()
```

#### 2.4 关键设计决策说明

**为什么每段用独立 Session？**
SQLite 的 Session 不支持并发写入。如果多个 coroutine 共用一个 Session，会触发 `database is locked` 或数据错乱。每段独立 Session + commit 后立即 close，SQLite 的文件锁粒度在每次 commit 时释放，不会互相阻塞。

**为什么不在并发过程中更新 batch_job 进度？**
多个 coroutine 同时写 batch_job.completed_segments 会产生竞争条件。改为 gather 完成后统一计算一次，简单可靠。前端轮询时看到的进度会在所有段完成后一次性跳到最终值，但这比引入锁更安全。

**gather 的顺序保证？**
`asyncio.gather(*tasks)` 的返回值与 tasks 列表顺序一致。segments 已按 index 排序，所以结果天然有序。合并阶段按 index 顺序遍历 segments 收集音频路径，无需额外排序。

### 3. `tests/test_batch_orchestration.py` — 新增测试

在文件末尾新增一个测试：

```python
def test_execute_batch_concurrent_respects_order(
    service, session: Session, seed_profile, seed_mock_binding
):
    """Concurrent execution preserves segment order in merged output."""
    now = utc_now_iso()
    batch_id = "batch_test_concurrent"
    batch_job = BatchJob(
        id=batch_id,
        mode="longtext",
        status=BatchStatus.pending,
        provider="mock",
        output_format="mp3",
        total_segments=5,
        silence_between_ms=0,
        config_json=json.dumps({
            "text": "一二三四五",
            "profile_id": "deep_night_programmer",
            "need_subtitle": False,
        }),
        created_at=now,
        updated_at=now,
    )
    session.add(batch_job)

    for i in range(5):
        seg = BatchSegment(
            id=f"seg_conc_{i}",
            batch_job_id=batch_id,
            index=i,
            text=f"并发测试段落{i}。",
            profile_id="deep_night_programmer",
            params_json="{}",
            status=BatchStatus.pending,
            created_at=now,
            updated_at=now,
        )
        session.add(seg)
    session.commit()

    asyncio.get_event_loop().run_until_complete(
        service.execute(session, batch_id)
    )

    # 刷新确保读到最新状态
    session.expire_all()
    segments = list(session.exec(
        select(BatchSegment).where(BatchSegment.batch_job_id == batch_id)
        .order_by(BatchSegment.index)
    ).all())

    assert len(segments) == 5
    assert all(s.status == BatchStatus.success for s in segments)
    # 验证 index 顺序正确（0, 1, 2, 3, 4）
    assert [s.index for s in segments] == [0, 1, 2, 3, 4]
    # 每段都有音频
    assert all(s.audio_asset_id is not None for s in segments)

    session.refresh(batch_job)
    assert batch_job.status == BatchStatus.success
    assert batch_job.completed_segments == 5
    assert batch_job.merged_audio_asset_id is not None
```

## 不要做的事

1. **不要修改 `_process_segment()` 方法本身** — 它保持不变，只是被新的 `_process_segment_isolated()` 包装调用
2. **不要在并发执行过程中更新 batch_job 的 completed_segments** — 统一在 gather 完成后计算
3. **不要修改前端文件** — 前端轮询逻辑无需改动
4. **不要修改 API 端点** — 接口保持不变
5. **不要修改 `_execute_with_session()`** — 入口保持不变
6. **不要使用线程池或 concurrent.futures** — 纯 asyncio 方案
7. **不要在 `_process_segment_isolated` 的独立 Session 中访问主 Session 的对象** — 会跨 Session 引用报错

## 验收标准

1. `python -m pytest tests/ -x -q` 全部通过（含新增测试）
2. 5 段批量任务执行后，合并音频段序与提交顺序一致
3. 单段失败不影响其他段并发执行
4. `batch_max_concurrency=1` 时行为与原串行一致（回退兼容）
5. retry_failed 在并发模式下正常工作

## 依赖

无新增依赖。
