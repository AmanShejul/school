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

export const schoolStats = [
  { label: 'Years of excellence', value: null, suffix: '' },
  { label: 'Learners', value: null, suffix: '+' },
  { label: 'Learning spaces', value: null, suffix: '+' },
  { label: 'Activities', value: null, suffix: '+' },
]

export const facilities = [
  { number: '01', title: 'Learning spaces', description: 'A considered place for focused learning.', icon: 'book', image: null, tone: 'facility-blue' },
  { number: '02', title: 'Discovery', description: 'Room for questions, ideas and reflection.', icon: 'compass', image: null, tone: 'facility-orange' },
  { number: '03', title: 'Exploration', description: 'A considered space for practical learning.', icon: 'flask', image: null, tone: 'facility-green' },
  { number: '04', title: 'Movement', description: 'A considered space for an active school day.', icon: 'activity', image: null, tone: 'facility-navy' },
  { number: '05', title: 'Making', description: 'Room to create, collaborate and express.', icon: 'palette', image: null, tone: 'facility-orange' },
  { number: '06', title: 'Campus', description: 'The setting for everyday school life.', icon: 'building', image: null, tone: 'facility-blue' },
]

export const initiatives = [
  { category: 'Learning', title: 'Ideas in motion', description: 'A space for verified learning stories and school initiatives.', image: null, link: '/academics', tone: 'initiative-blue' },
  { category: 'Creativity', title: 'Making meaning', description: 'A place to share verified creative work and community initiatives.', image: null, link: '/student-life', tone: 'initiative-orange' },
  { category: 'Wellbeing', title: 'Growing together', description: 'A space for verified activities that support a balanced school life.', image: null, link: '/student-life', tone: 'initiative-green' },
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
