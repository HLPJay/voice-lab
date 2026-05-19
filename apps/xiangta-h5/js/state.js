"use strict";

const state = {
  mode: "formal",
  screen: "home",
  bootstrap: null,
  selectedRecipient: null,
  selectedScene: null,
  suggestions: [],
  suggestionMeta: null,
  selectedIndex: -1,
  selectedStyle: "gentle",
  selectedVoice: "female-gentle",
  selectedTone: "gentle",
  finalText: "",
  ttsTask: null,
  ttsResult: null,
  ttsPollToken: 0,
  letters: [],
  coreProfiles: [],
  voiceBindingStatus: null,  // loaded from GET /voice-bindings/status
  resultSaved: false,
  resultSavedLetterId: null,
  resultSavedLetter: null,
  resultFavorited: false,
  historyReturnTo: "home",
  // History page state
  historyFilter: "all",
  historySearchOpen: false,
  historySearchQuery: "",
  activeHistoryLetterId: null,
  historyAudioPlaying: false,
  historyAudioCurrentTime: 0,
  historyAudioDuration: 0,
  historyAudioListenersBound: false,
  // Letter detail state
  activeLetterDetailId: null,
  activeLetterDetail: null,
  letterDetailFavoritedMap: {},
  // Demo fixture flow — set by fillSceneExample(), cleared when rawText changes
  demoFixtureKey: null,
  demoFixtureActive: false,
};
