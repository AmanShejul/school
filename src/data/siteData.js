// Central content model for verified school information.
export const imageAssets = {
  logo: '/assets/logo/jigisha-logo.png',
  heroImage: '/assets/hero/jigisha-school-enhanced.jpg',
  campusImages: [],
  classroomImages: [],
  studentImages: [],
  facultyImages: [],
  eventImages: [],
  achievementImages: [],
  galleryImages: ['/assets/hero/jigisha-school-enhanced.jpg'],
}

export const schoolLocation = {
  name: 'Jigisha International School',
  address: 'M-1 Jigisha, N-7, CIDCO, Chhatrapati Sambhajinagar, Maharashtra 431003, India',
  mapsQuery: 'Jigisha International School, M-1 Jigisha, N-7, CIDCO, Chhatrapati Sambhajinagar, Maharashtra 431003, India',
}

export const schoolStats = [
  { label: 'Years of excellence', value: null, suffix: '' },
  { label: 'Learners', value: null, suffix: '+' },
  { label: 'Learning spaces', value: null, suffix: '+' },
  { label: 'Activities', value: null, suffix: '+' },
]

export const learningSpaces = [
  {
    id: 'learning', number: '01', title: 'Learning spaces',
    shortDescription: 'A place to learn, explore ideas and grow.',
    description: '', details: [], image: null, gallery: [], icon: 'book',
    tone: 'facility-blue', href: '/academics', cta: 'Explore learning',
  },
  {
    id: 'discovery', number: '02', title: 'Discovery',
    shortDescription: 'Questions, ideas and new ways to understand the world.',
    description: '', details: [], image: null, gallery: [], icon: 'compass',
    tone: 'facility-orange', href: '/academics', cta: 'Discover more',
  },
  {
    id: 'exploration', number: '03', title: 'Exploration',
    shortDescription: 'Opportunities to look closer, try things and keep learning.',
    description: '', details: [], image: null, gallery: [], icon: 'flask',
    tone: 'facility-green', href: '/academics', cta: 'Explore more',
  },
  {
    id: 'movement', number: '04', title: 'Movement',
    shortDescription: 'Active learning, play and a healthy rhythm through the school day.',
    description: '', details: [], image: null, gallery: [], icon: 'activity',
    tone: 'facility-navy', href: '/student-life', cta: 'Explore student life',
  },
  {
    id: 'making', number: '05', title: 'Making',
    shortDescription: 'Ideas take shape through creativity, practice and expression.',
    description: '', details: [], image: null, gallery: [], icon: 'palette',
    tone: 'facility-orange', href: '/student-life', cta: 'Explore creativity',
  },
  {
    id: 'campus', number: '06', title: 'Campus',
    shortDescription: 'The school environment where everyday learning happens.',
    description: '', details: [], image: null, gallery: [], icon: 'building',
    tone: 'facility-blue', href: '/gallery', cta: 'View the gallery',
  },
]

export const galleryVisuals = [
  { category: 'Campus', title: 'A place to belong', tone: 'gallery-blue' },
  { category: 'Learning', title: 'Curiosity in action', tone: 'gallery-orange' },
  { category: 'Community', title: 'Growing together', tone: 'gallery-green' },
  { category: 'Celebration', title: 'Moments that matter', tone: 'gallery-navy' },
  { category: 'Sport', title: 'Move with purpose', tone: 'gallery-yellow' },
  { category: 'Arts', title: 'Find your voice', tone: 'gallery-blue' },
]

// Keep this empty until verified school news or events are available.
export const newsItems = []

// Add only verified review objects here when they are approved for publication.
export const reviews = []
