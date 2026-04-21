export const mockDocuments = [
  {
    id: "doc-01",
    name: "Biology 101 - Cellular Matrix",
    type: "pdf",
    size: "2.4 MB",
    status: "Ready",
    dateAdded: "2 hours ago",
    pages: 42,
  },
  {
    id: "doc-02",
    name: "History Notes: Renaissance",
    type: "docx",
    size: "1.1 MB",
    status: "Ready",
    dateAdded: "Yesterday",
    pages: 15,
  },
  {
    id: "doc-03",
    name: "Chemistry Lab Results",
    type: "pdf",
    size: "5.8 MB",
    status: "Processing",
    dateAdded: "Just now",
    pages: 12,
  },
];

export const mockChats = [
  {
    id: "chat-01",
    role: "user",
    content: "Explain the process of cellular respiration as if I am 5.",
  },
  {
    id: "chat-02",
    role: "ai",
    content: "Imagine your body is a tiny factory! Cellular respiration is how the factory takes the food you eat (sugar) and uses the air you breathe (oxygen) to create energy. This energy lets you run, jump, and play! The factory also produces a little bit of water and carbon dioxide (which you breathe out) as leftovers.",
    sources: [
      { page: 12, docId: "doc-01", docName: "Biology 101 - Cellular Matrix" },
      { page: 14, docId: "doc-01", docName: "Biology 101 - Cellular Matrix" }
    ]
  },
  {
    id: "chat-03",
    role: "user",
    content: "What are the three main stages?",
  },
  {
    id: "chat-04",
    role: "ai",
    content: "Great question! The three main stages are:\n\n1. **Glycolysis**: Breaking the sugar down right at the factory door.\n2. **Krebs Cycle (Citric Acid Cycle)**: Mixing it up inside the factory to get energetic particles ready.\n3. **Electron Transport Chain**: The final assembly line that produces almost all of the actual energy (ATP).",
    sources: [
      { page: 18, docId: "doc-01", docName: "Biology 101 - Cellular Matrix" }
    ]
  }
];

export const mockRecentChatsList = [
  { id: "rc-1", title: "Cellular Respiration Process", time: "2h ago" },
  { id: "rc-2", title: "Renaissance Art Movements", time: "Yesterday" },
  { id: "rc-3", title: "Organic Chemistry Midterm Prep", time: "Oct 12" },
];

export const mockQuizQuestions = [
  {
    id: "q1",
    question: "Where in the cell does Glycolysis occur?",
    options: ["Mitochondria", "Nucleus", "Cytoplasm", "Endoplasmic Reticulum"],
    correctAnswer: 2, // Index of Cytoplasm
  },
  {
    id: "q2",
    question: "What is the primary product of the Electron Transport Chain?",
    options: ["Glucose", "ATP", "Lactic Acid", "Oxygen"],
    correctAnswer: 1, // Index of ATP
  }
];

export const mockProgressData = {
  accuracy: [80, 85, 82, 88, 92, 90, 95], // Trend over 7 weeks/quizzes
  weakTopics: [
    { topic: "Krebs Cycle", score: 65 },
    { topic: "Enzyme Kinetics", score: 72 },
    { topic: "Meiosis Origins", score: 78 }
  ]
};
