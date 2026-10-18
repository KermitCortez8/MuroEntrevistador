const jobTemplateEl = document.getElementById('jobTemplate');
const startInterviewEl = document.getElementById('startInterview');
const interviewSectionEl = document.getElementById('interviewSection');
const historySectionEl = document.getElementById('historySection');
const currentQuestionEl = document.getElementById('currentQuestion');
const answerTextEl = document.getElementById('answerText');
const submitAnswerEl = document.getElementById('submitAnswer');
const historyListEl = document.getElementById('historyList');
const recordAnswerEl = document.getElementById('recordAnswer');
const recordStatusEl = document.getElementById('recordStatus');

const baseQuestions = [
  '¿Cómo diseñarías una API REST escalable para una aplicación con miles de usuarios concurrentes?',
  '¿Qué estrategias usarías para asegurar la calidad del software en un equipo ágil?',
  'Explícame una situación en la que tuviste que depurar un problema complejo en producción.',
  '¿Cómo priorizas seguridad, rendimiento y mantenibilidad al desarrollar una solución?',
  '¿Qué métricas técnicas usarías para evaluar el éxito de una arquitectura de software?',
];

const categoryQuestions = {
  backend: [
    '¿Qué diferencias clave hay entre una arquitectura monolítica y microservicios, y cuándo elegirías cada una?',
    '¿Cómo implementarías autenticación y autorización segura en una API?',
  ],
  frontend: [
    '¿Cómo optimizarías el rendimiento de una interfaz web con muchos componentes dinámicos?',
    '¿Qué prácticas sigues para construir interfaces accesibles y mantenibles?',
  ],
  databases: [
    '¿Cuándo usarías una base de datos SQL frente a NoSQL en un sistema empresarial?',
    '¿Cómo diseñarías índices y consultas para mejorar el rendimiento de una base de datos?',
  ],
  cloud: [
    '¿Cómo desplegarías una aplicación en la nube con alta disponibilidad y tolerancia a fallos?',
    '¿Qué ventajas y riesgos ves en usar contenedores y orquestación (por ejemplo, Docker/Kubernetes)?',
  ],
  testing: [
    '¿Cómo estructurarías una estrategia de testing que combine unitarios, integración y E2E?',
    '¿Qué haces cuando un test es inestable (flaky) en CI/CD?',
  ],
  algorithms: [
    '¿Cómo analizarías la complejidad temporal y espacial de una solución antes de implementarla?',
    '¿Puedes contar un caso donde elegiste una estructura de datos específica para optimizar rendimiento?',
  ],
  security: [
    '¿Cómo previenes vulnerabilidades comunes como inyección SQL, XSS o CSRF?',
    '¿Qué controles implementarías para proteger datos sensibles en tránsito y en reposo?',
  ],
};

const keywordToCategory = {
  api: 'backend',
  backend: 'backend',
  microservicios: 'backend',
  front: 'frontend',
  frontend: 'frontend',
  react: 'frontend',
  angular: 'frontend',
  sql: 'databases',
  nosql: 'databases',
  base: 'databases',
  datos: 'databases',
  aws: 'cloud',
  azure: 'cloud',
  gcp: 'cloud',
  cloud: 'cloud',
  docker: 'cloud',
  kubernetes: 'cloud',
  test: 'testing',
  testing: 'testing',
  qa: 'testing',
  algoritmo: 'algorithms',
  estructura: 'algorithms',
  seguridad: 'security',
  security: 'security',
  ciberseguridad: 'security',
};

let questions = [];
let answers = [];
let currentIndex = 0;
let recognition;

function unique(array) {
  return [...new Set(array)];
}

function detectCategories(text) {
  const lowered = text.toLowerCase();
  const found = Object.entries(keywordToCategory)
    .filter(([keyword]) => lowered.includes(keyword))
    .map(([, category]) => category);

  return unique(found);
}

function buildQuestionsFromTemplate(templateText) {
  const detected = detectCategories(templateText);
  const specific = detected.flatMap((category) => categoryQuestions[category] || []);
  const combined = unique([...specific, ...baseQuestions]);
  return combined.slice(0, 8);
}

function speak(text) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'es-ES';
  window.speechSynthesis.speak(utterance);
}

function renderQuestion() {
  const question = questions[currentIndex];
  if (!question) {
    currentQuestionEl.textContent = 'Entrevista finalizada. ¡Buen trabajo!';
    answerTextEl.disabled = true;
    submitAnswerEl.disabled = true;
    recordAnswerEl.disabled = true;
    speak('Entrevista finalizada. Buen trabajo.');
    return;
  }

  currentQuestionEl.textContent = question;
  answerTextEl.value = '';
  speak(question);
}

function addHistoryItem(question, answer) {
  const li = document.createElement('li');
  li.innerHTML = `<strong>Pregunta:</strong> ${question}<br /><strong>Respuesta:</strong> ${answer}`;
  historyListEl.appendChild(li);
}

function startInterview() {
  const template = jobTemplateEl.value.trim();
  if (!template) {
    alert('Debes ingresar una plantilla u oferta laboral antes de iniciar.');
    return;
  }

  questions = buildQuestionsFromTemplate(template);
  answers = [];
  currentIndex = 0;
  historyListEl.innerHTML = '';
  answerTextEl.disabled = false;
  submitAnswerEl.disabled = false;
  recordAnswerEl.disabled = false;
  interviewSectionEl.hidden = false;
  historySectionEl.hidden = false;
  renderQuestion();
}

function submitAnswer() {
  const answer = answerTextEl.value.trim();
  if (!answer) {
    alert('Por favor, responde antes de continuar.');
    return;
  }

  const question = questions[currentIndex];
  answers.push({ question, answer });
  addHistoryItem(question, answer);
  currentIndex += 1;
  renderQuestion();
}

function setupSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    recordAnswerEl.disabled = true;
    recordStatusEl.textContent = 'Reconocimiento de voz no soportado en este navegador.';
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = 'es-ES';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    recordStatusEl.textContent = 'Escuchando...';
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    answerTextEl.value = transcript;
    recordStatusEl.textContent = 'Audio transcrito. Puedes editar y enviar.';
  };

  recognition.onerror = () => {
    recordStatusEl.textContent = 'No fue posible transcribir el audio. Intenta de nuevo.';
  };

  recognition.onend = () => {
    if (recordStatusEl.textContent === 'Escuchando...') {
      recordStatusEl.textContent = 'Grabación finalizada.';
    }
  };
}

startInterviewEl.addEventListener('click', startInterview);
submitAnswerEl.addEventListener('click', submitAnswer);
recordAnswerEl.addEventListener('click', () => {
  if (recognition) recognition.start();
});

setupSpeechRecognition();
