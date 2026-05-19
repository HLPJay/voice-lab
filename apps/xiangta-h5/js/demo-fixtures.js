"use strict";

// Demo fixture flow — local preset suggestions for the built-in scene examples.
// Used by generateSuggestions() when demoFixtureActive is true and rawText matches exactly.
// rawText must match FLOW_EXAMPLES[scene].rawText so the bypass fires after clicking "用一个例子开始".

const DEMO_FIXTURES = {
  miss: {
    recipient: "lover",
    scene: "miss",
    rawText: "今天下雨了，我突然想起你。那天一起淋雨的时候，其实我心里很安静，也很想靠近你。",
    suggestionMeta: {
      summary: "你想把那一刻的靠近感说出来，不是索取，只是想告诉他/她那一刻你很安心。",
      intent: "让对方感受到被想念，而不是被需要",
      source: "demo_fixture",
      degraded: false,
      latencyMs: 0,
    },
    suggestions: [
      {
        style: "restrained",
        styleLabel: "克制版",
        fitsFor: "适合不想把话说得太重、太黏腻的时候",
        text: "今天下雨，我想起你了。那天一起淋雨，我心里其实很安静。",
      },
      {
        style: "gentle",
        styleLabel: "温柔版",
        fitsFor: "适合想念但不知道怎么开口的时候",
        text: "今天下雨了，我突然想起那次我们一起淋雨。那时候我心里很安静，也很想靠近你。就是随便想想，不用回复。",
      },
      {
        style: "sincere",
        styleLabel: "真诚版",
        fitsFor: "适合想认真说出当时感受的时候",
        text: "今天下雨，我想起那次我们一起淋雨的那天。其实那时候我心里很平静，但同时又很想靠近你。一直没说出来，今天想告诉你。",
      },
    ],
    preferredIndex: 1,
    preferredVoice: "female-gentle",
    preferredTone: "gentle",
    title: "雨天的想念",
  },

  sorry: {
    recipient: "lover",
    scene: "sorry",
    rawText: "昨天那句话我说重了。后来我一直在想，我不是想伤害你，只是当时没处理好自己的情绪。",
    suggestionMeta: {
      summary: "你想为昨天的话道歉，但不想说成找借口——你希望对方知道你看到了自己的问题。",
      intent: "让道歉听起来真诚，而不是解释",
      source: "demo_fixture",
      degraded: false,
      latencyMs: 0,
    },
    suggestions: [
      {
        style: "restrained",
        styleLabel: "克制版",
        fitsFor: "适合不想说太多、直接认错的时候",
        text: "昨天那句话说重了，对不起。我不是想伤害你，只是当时情绪没处理好。",
      },
      {
        style: "gentle",
        styleLabel: "温柔版",
        fitsFor: "适合想好好说清楚、又不想让对方觉得沉重的时候",
        text: "昨天那句话，我后来一直在想。我不是想伤害你，真的，只是当时自己的情绪没控制好，没说好。对不起，希望你还好。",
      },
      {
        style: "sincere",
        styleLabel: "真诚版",
        fitsFor: "适合想认真道歉、说清楚自己问题的时候",
        text: "昨天那句话说重了，我知道。后来反复想，我不是想伤害你，是我当时没有处理好自己的情绪，把它发在了你身上。这是我的问题，不是你的。对不起。",
      },
    ],
    preferredIndex: 1,
    preferredVoice: "male-gentle",
    preferredTone: "sincere",
    title: "认真的道歉",
  },

  thanks: {
    recipient: "friend",
    scene: "thanks",
    rawText: "那天你没有问太多，就一直在我身边。后来我想了很久，还是想认真跟你说一声谢谢。",
    suggestionMeta: {
      summary: "你想感谢一个朋友的陪伴——他/她没有多问，只是在你身边。这种陪伴对你很重要。",
      intent: "让谢谢说得更有分量，更像是真正在意",
      source: "demo_fixture",
      degraded: false,
      latencyMs: 0,
    },
    suggestions: [
      {
        style: "restrained",
        styleLabel: "克制版",
        fitsFor: "适合不擅长说谢谢、但真的很感激的时候",
        text: "那天谢谢你在。你没有问太多，这对我很重要。",
      },
      {
        style: "gentle",
        styleLabel: "温柔版",
        fitsFor: "适合想把感谢说得暖一些、更像一封信的时候",
        text: "那天你没有问我太多，就一直在旁边。后来我想了很久，觉得你那种陪伴对我来说很珍贵。谢谢你，认真的那种谢谢。",
      },
      {
        style: "sincere",
        styleLabel: "真诚版",
        fitsFor: "适合想认真表达、让对方知道自己有多在意的时候",
        text: "那天你没有问太多，只是一直在我身边。那种“不需要解释，你就在”的感觉，我一直记得。后来想了很久，想认真跟你说：谢谢你，真的谢谢你。",
      },
    ],
    preferredIndex: 1,
    preferredVoice: "female-gentle",
    preferredTone: "gentle",
    title: "一句迟到的谢谢",
  },

  comfort: {
    recipient: "friend",
    scene: "comfort",
    rawText: "如果你今天很累，就先不用解释。想说的时候我会听，不想说也没有关系。",
    suggestionMeta: {
      summary: "你想让对方知道不需要解释，你在就够了——这是一种低压力的陪伴。",
      intent: "让安慰听起来不像压力，更像一个轻轻放下的手",
      source: "demo_fixture",
      degraded: false,
      latencyMs: 0,
    },
    suggestions: [
      {
        style: "restrained",
        styleLabel: "克制版",
        fitsFor: "适合不想把话说多、只想让对方感觉到在的时候",
        text: "如果今天很累，不用解释。我在。",
      },
      {
        style: "gentle",
        styleLabel: "温柔版",
        fitsFor: "适合想轻轻说、不给对方压力的时候",
        text: "如果你今天很累，不用解释，也不用撑着说话。想说的时候我会听，不想说，就放着也好。我在就行了。",
      },
      {
        style: "sincere",
        styleLabel: "真诚版",
        fitsFor: "适合真的很担心对方、想认真说清楚自己想法的时候",
        text: "不管你今天发生了什么，都不需要跟我解释。你随时可以说，也可以不说。我想让你知道，不管哪种，我都在这里。",
      },
    ],
    preferredIndex: 1,
    preferredVoice: "male-gentle",
    preferredTone: "restrained",
    title: "陪你一会儿",
  },

  night: {
    recipient: "lover",
    scene: "night",
    rawText: "今天先到这里吧。别再想工作和烦心的事了，先把自己交给夜晚，好好睡一觉。",
    suggestionMeta: {
      summary: "你想在睡前说一句晚安，带着一点温柔，让对方把今天放下。",
      intent: "让晚安轻一点、暖一点，像帮对方盖上被子",
      source: "demo_fixture",
      degraded: false,
      latencyMs: 0,
    },
    suggestions: [
      {
        style: "restrained",
        styleLabel: "克制版",
        fitsFor: "适合睡前不想说太多、就一句晚安的时候",
        text: "今天到这里吧。别想了，好好睡。晚安。",
      },
      {
        style: "gentle",
        styleLabel: "温柔版",
        fitsFor: "适合想让对方觉得被关心、轻轻睡去的时候",
        text: "今天先到这里吧。工作和烦心的事，先放到明天去。把自己交给夜晚，好好睡一觉。晚安，好梦。",
      },
      {
        style: "sincere",
        styleLabel: "真诚版",
        fitsFor: "适合对方今天状态不太好、想认真说一声晚安的时候",
        text: "今天辛苦了。不管发生了什么，先停下来。别再想工作，别再想那些烦心事——你已经够努力了。交给夜晚，好好休息。晚安。",
      },
    ],
    preferredIndex: 1,
    preferredVoice: "female-gentle",
    preferredTone: "gentle",
    title: "今晚，说晚安",
  },
};
