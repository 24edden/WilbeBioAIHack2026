// Copy this folder into your frontend public directory.
const pets = {
  "generic-scientist": {
    "label": "Generic scientist",
    "gif": "generic-scientist.gif",
    "webp": "generic-scientist.webp",
    "png": "generic-scientist.png"
  },
  "bioinformatician": {
    "label": "Bioinformatician",
    "gif": "bioinformatician.gif",
    "webp": "bioinformatician.webp",
    "png": "bioinformatician.png"
  },
  "statistician": {
    "label": "Statistician",
    "gif": "statistician.gif",
    "webp": "statistician.webp",
    "png": "statistician.png"
  },
  "clinical-scientist": {
    "label": "Clinical scientist",
    "gif": "clinical-scientist.gif",
    "webp": "clinical-scientist.webp",
    "png": "clinical-scientist.png"
  },
  "computational-biologist": {
    "label": "Computational biologist",
    "gif": "computational-biologist.gif",
    "webp": "computational-biologist.webp",
    "png": "computational-biologist.png"
  },
  "epidemiologist": {
    "label": "Epidemiologist",
    "gif": "epidemiologist.gif",
    "webp": "epidemiologist.webp",
    "png": "epidemiologist.png"
  },
  "immunologist": {
    "label": "Immunologist",
    "gif": "immunologist.gif",
    "webp": "immunologist.webp",
    "png": "immunologist.png"
  },
  "synthetic-biologist": {
    "label": "Synthetic biologist",
    "gif": "synthetic-biologist.gif",
    "webp": "synthetic-biologist.webp",
    "png": "synthetic-biologist.png"
  },
  "pharmacologist": {
    "label": "Pharmacologist",
    "gif": "pharmacologist.gif",
    "webp": "pharmacologist.webp",
    "png": "pharmacologist.png"
  }
};

/** Unknown, empty, or missing roles use the generic scientist. */
export function getScientistPet(role, options = {}) {
  const { basePath = '/scientist-pets', format = 'webp', reducedMotion = false } = options;
  const key = typeof role === 'string'
    ? role.trim().toLowerCase().replace(/[\s_]+/g, '-')
    : '';
  const id = Object.prototype.hasOwnProperty.call(pets, key) ? key : 'generic-scientist';
  const extension = reducedMotion ? 'png' : format;
  if (!['webp', 'gif', 'png'].includes(extension)) {
    throw new TypeError('format must be webp, gif, or png');
  }
  const base = basePath.replace(/\/+$/, '');
  return `${base}/${pets[id][extension]}`;
}
