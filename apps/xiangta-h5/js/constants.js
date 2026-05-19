"use strict";

const API_BASE = "";
const STEP_LABELS = ["整理想法", "挑选表达", "生成语音"];
const PLACEHOLDER_PROFILE = "<coreProfileIdFromCoreProfiles>";

const RECIPIENT_META = {
  lover: {
    label: "恋人",
    hint: "想他 / 想她",
    icon: '<svg width="26" height="26" viewBox="0 0 26 26" fill="none"><circle cx="9.5" cy="13" r="5.5" stroke="currentColor" stroke-width="1.2" opacity="0.6"></circle><circle cx="16.5" cy="13" r="5.5" stroke="currentColor" stroke-width="1.2"></circle><circle cx="13" cy="13" r="1.1" fill="currentColor"></circle></svg>',
  },
  family: {
    label: "父母",
    hint: "爸爸 / 妈妈",
    icon: '<svg width="26" height="26" viewBox="0 0 26 26" fill="none"><path d="M4 21v-9.2L13 5l9 6.8V21" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"></path><path d="M10 21v-5h6v5" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"></path></svg>',
  },
  friend: {
    label: "朋友",
    hint: "老朋友 / 新朋友",
    icon: '<svg width="26" height="26" viewBox="0 0 26 26" fill="none"><path d="M7 18v-2.2A3.8 3.8 0 0110.8 12h4.4A3.8 3.8 0 0119 15.8V18M10 10.5a2.5 2.5 0 105 0 2.5 2.5 0 00-5 0z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"></path></svg>',
  },
  self: {
    label: "自己",
    hint: "写给自己",
    icon: '<svg width="26" height="26" viewBox="0 0 26 26" fill="none"><circle cx="13" cy="13" r="8.5" stroke="currentColor" stroke-width="1.2" opacity="0.58"></circle><circle cx="13" cy="13" r="2.4" fill="currentColor"></circle></svg>',
  },
};

const SCENE_META = {
  miss: { label: "想念", hint: "不知不觉就想起你" },
  sorry: { label: "道歉", hint: "那天，是我不好" },
  thanks: { label: "感谢", hint: "一直没有好好说" },
  comfort: { label: "安慰", hint: "陪你一会儿" },
  night: { label: "晚安", hint: "睡前的一句话" },
};

const RAW_EXAMPLES = {
  miss: "今天下雨了，我突然想起你。那天一起淋雨的时候，其实我心里很安静，也很想靠近你。",
  sorry: "昨天那句话我说重了。后来我一直在想，我不是想伤害你，只是当时没处理好自己的情绪。",
  thanks: "那天你没有问太多，就一直在我身边。后来我想了很久，还是想认真跟你说一声谢谢。",
  comfort: "如果你今天很累，就先不用解释。想说的时候我会听，不想说也没有关系。",
  night: "今天先到这里吧。别再想工作和烦心事了，先把自己交给夜晚，好好睡一觉。",
};

const GUIDANCE_PROMPTS = {
  miss: [
    "你希望 Ta 听完之后，感受到什么？",
    "有没有不想说得太重、太直接的部分？",
    "你们上一次好好说话，是什么时候？",
  ],
  sorry: [
    "你想为哪件事认真道歉？",
    "你希望对方知道，你看到了哪些做得不好的地方？",
    "你不想把这段话说成找借口，最该避开的是什么？",
  ],
  thanks: [
    "你最想感谢的是哪一个细节？",
    "那件事对你来说，到底意味着什么？",
    "有没有一直没说出口的那一句谢谢？",
  ],
  comfort: [
    "对方现在在经历什么？",
    "你想让对方感受到被怎样接住？",
    "有什么是你不想说成说教的？",
  ],
  night: [
    "今天的晚安里，你最想留下什么感觉？",
    "有没有一句话是想让对方放松下来的？",
    "今晚不说重话的话，你会怎么收尾？",
  ],
};

const STYLE_LABELS = {
  restrained: "克制版",
  gentle: "温柔版",
  sincere: "真诚版",
};

const TONE_META = [
  { id: "restrained", label: "克制" },
  { id: "gentle", label: "温柔" },
  { id: "sincere", label: "真诚" },
  { id: "whisper", label: "轻声" },
  { id: "bedtime", label: "睡前" },
];

// Full-flow examples: when user clicks "用一个例子开始"，pre-fill entire 3-step flow
const FLOW_EXAMPLES = {
  miss: {
    recipient: "lover",
    scene: "miss",
    rawText: "今天下雨了，我突然想起你。那天一起淋雨的时候，其实我心里很安静，也很想靠近你。",
    preferredStyle: "gentle",
    preferredVoice: "female-gentle",
    preferredTone: "gentle",
    title: "雨天的想念",
    sampleGoal: "把模糊的想念说成一句温柔的话",
  },
  sorry: {
    recipient: "lover",
    scene: "sorry",
    rawText: "昨天那句话我说重了。后来我一直在想，我不是想伤害你，只是当时没处理好自己的情绪。",
    preferredStyle: "sincere",
    preferredVoice: "male-gentle",
    preferredTone: "sincere",
    title: "认真的道歉",
    sampleGoal: "把道歉说成更真诚、更清楚的一句",
  },
  thanks: {
    recipient: "friend",
    scene: "thanks",
    rawText: "那天你没有问太多，就一直在我身边。后来我想了很久，还是想认真跟你说一声谢谢。",
    preferredStyle: "gentle",
    preferredVoice: "female-gentle",
    preferredTone: "gentle",
    title: "一句迟到的谢谢",
    sampleGoal: "把感谢说成温暖的陪伴",
  },
  comfort: {
    recipient: "friend",
    scene: "comfort",
    rawText: "如果你今天很累，就先不用解释。想说的时候我会听，不想说也没有关系。",
    preferredStyle: "restrained",
    preferredVoice: "male-gentle",
    preferredTone: "restrained",
    title: "陪你一会儿",
    sampleGoal: "把安慰说成不带压力的陪伴",
  },
  night: {
    recipient: "lover",
    scene: "night",
    rawText: "今天先到这里吧。别再想工作和烦心的事了，先把自己交给夜晚，好好睡一觉。",
    preferredStyle: "gentle",
    preferredVoice: "female-gentle",
    preferredTone: "gentle",
    title: "今晚，说晚安",
    sampleGoal: "把晚安说成温柔的结束语",
  },
};
