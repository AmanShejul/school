import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion, useInView, useReducedMotion } from 'framer-motion'
import { facilities, galleryPlaceholders, initiatives, newsPlaceholders, schoolStats } from './data/siteData'

const logo = '/assets/jigisha-logo.png'

const navItems = [
  { label: 'About', href: '/about', children: ['About school', 'Vision & mission', 'Principalâ€™s message'] },
  { label: 'Academics', href: '/academics', children: ['Curriculum', 'Teaching approach', 'Activities'] },
  { label: 'Why Jigisha', href: '/why-jigisha', children: ['Our difference', 'School values', 'Learning spaces'] },
  { label: 'Admissions', href: '/admissions', children: ['Admission process', 'Required documents', 'Enquiry'] },
  { label: 'Student life', href: '/student-life', children: ['Events', 'Sports', 'Arts & culture'] },
  { label: 'Explore', href: '/gallery', children: ['Gallery', 'Achievements', 'News'] },
]

const journey = [
  { number: '01', kicker: 'Think deeply', title: 'Academic excellence', text: 'A thoughtful learning culture built around questions, clarity and confidence.', color: 'blue' },
  { number: '02', kicker: 'Make boldly', title: 'Creative expression', text: 'Room to explore ideas through art, design, performance and making.', color: 'orange' },
  { number: '03', kicker: 'Move freely', title: 'Active wellbeing', text: 'Learning that makes space for movement, teamwork and a healthy rhythm.', color: 'green' },
  { number: '04', kicker: 'Grow together', title: 'Character & care', text: 'The everyday habits of respect, responsibility and belonging.', color: 'navy' },
  { number: '05', kicker: 'Look ahead', title: 'Future readiness', text: 'Curiosity and practical confidence for a changing world.', color: 'lime' },
  { number: '06', kicker: 'Find your voice', title: 'Leadership', text: 'Opportunities to participate, listen, contribute and lead with purpose.', color: 'sun' },
]

const pillars = [
  ['01', 'Curiosity', 'We keep asking better questions.'],
  ['02', 'Integrity', 'We do the right thing, even when no one is watching.'],
  ['03', 'Courage', 'We try, learn, adapt and try again.'],
  ['04', 'Community', 'We grow through respect and shared responsibility.'],
]

const faqs = [
  ['Where is Jigisha International School located?', 'Our school is located at M-1 Jigisha, N-7, CIDCO, Chhatrapati Sambhajinagar, Maharashtra 431003, India.'],
  ['How can I enquire about admissions?', 'Use the enquiry form on this website. The school team can then share the current admission process and availability with you.'],
  ['Which grades does the school offer?', 'Grade availability is best confirmed directly with the school team. Submit an enquiry and we will help you find the right information.'],
  ['What information should I keep ready?', 'For a first enquiry, your parent name, student name, preferred grade, email and mobile number are enough.'],
]

function App() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const path = window.location.pathname

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    document.title = path === '/' ? 'Jigisha International School' : `${pageTitle(path)} Â· Jigisha International School`
    window.scrollTo(0, 0)
  }, [path])

  return <>
    <div className="utility-bar"><div className="shell utility-inner"><span>JIGISHA INTERNATIONAL SCHOOL</span><span className="utility-location">N-7, CIDCO Â· Chhatrapati Sambhajinagar</span><a href="#enquiry">Start an enquiry <span aria-hidden="true">â†—</span></a></div></div>
    <header className={`site-header ${scrolled ? 'is-scrolled' : ''}`}>
      <div className="shell nav-inner">
        <a className="brand" href="/" aria-label="Jigisha International School home"><span className="brand-mark"><img src={logo} alt="" /></span><span className="brand-copy"><strong>Jigisha</strong><em>International School</em></span></a>
        <nav className={`desktop-nav ${menuOpen ? 'mobile-open' : ''}`} aria-label="Primary navigation">
          <a href="/" className="nav-home">Home</a>
          {navItems.map(item => <div className="nav-dropdown" key={item.label}><a href={item.href}>{item.label}<span className="chevron">âŒ„</span></a><div className="dropdown-menu">{item.children.map(child => <a key={child} href={`${item.href}#${child.toLowerCase().replaceAll(' ', '-')}`}>{child}</a>)}</div></div>)}
          <a className="nav-contact" href="/contact">Contact <span aria-hidden="true">â†—</span></a>
        </nav>
        <a className="button button-small nav-cta" href="#enquiry">Enquire now <span aria-hidden="true">â†—</span></a>
        <button className={`menu-toggle ${menuOpen ? 'open' : ''}`} onClick={() => setMenuOpen(!menuOpen)} aria-label={menuOpen ? 'Close navigation' : 'Open navigation'} aria-expanded={menuOpen}><span></span><span></span></button>
      </div>
    </header>
    {path === '/' ? <Home /> : <InnerPage path={path} />}
    <Footer />
  </>
}

function Home() {
  return <main>
    <section className="hero section-dark">
      <div className="hero-orbit orbit-one"></div><div className="hero-orbit orbit-two"></div>
      <div className="shell hero-grid">
        <div className="hero-copy reveal"><p className="eyebrow eyebrow-light"><span></span> School for the whole child</p><h1>Learning today.<br /><i>Leading</i> tomorrow.</h1><p className="hero-intro">A welcoming learning community in Chhatrapati Sambhajinagar, where curiosity becomes confidence and every learner is encouraged to find their own way forward.</p><div className="hero-actions"><a className="button button-orange" href="#enquiry">Explore our school <span>â†—</span></a><a className="text-link light-link" href="/admissions">Admissions <span>â†—</span></a></div></div>
        <div className="hero-visual reveal delay-one"><div className="hero-frame"><div className="frame-accent"></div><div className="frame-inner"><span className="frame-label">Jigisha / 01</span><img src={logo} alt="Jigisha International School official crest" /><div className="frame-note">A place to<br /><strong>belong & grow</strong></div></div></div><div className="hero-stamp"> <strong>J</strong><span>Chhatrapati<br />Sambhajinagar</span></div></div>
      </div>
      <div className="hero-footer shell"><span>Scroll to explore</span><span className="scroll-line"></span><span>01 / 04</span></div>
    </section>

    <section className="quick-actions"><div className="shell quick-grid"><a href="/about"><span className="action-number">01</span><strong>Discover Jigisha</strong><span className="action-arrow">â†—</span></a><a href="/academics"><span className="action-number">02</span><strong>Learning at Jigisha</strong><span className="action-arrow">â†—</span></a><a href="/admissions"><span className="action-number">03</span><strong>Join our community</strong><span className="action-arrow">â†—</span></a><a href="/contact"><span className="action-number">04</span><strong>Find us</strong><span className="action-arrow">â†—</span></a></div></section>

    <section className="section intro-section"><div className="shell intro-grid"><div className="intro-aside reveal"><p className="eyebrow"><span></span> About Jigisha</p><p className="aside-number">01<span>/</span>04</p></div><div className="intro-content reveal delay-one"><h2>Where learning meets <i>curiosity,</i> creativity and character.</h2><p>Jigisha International School is a place for thoughtful beginnings and brave next steps. Our visual identity speaks of energy, movement and possibility; our school experience is being shaped around the same promise.</p><a className="text-link" href="/about">Read our story <span>â†—</span></a></div><div className="intro-art reveal delay-two"><div className="art-disc"><img src={logo} alt="" /></div><span className="art-caption">Official school identity<br />Jigisha International School</span></div></div></section>
    <StatsSection />

    <section className="section journey-section section-paper"><div className="shell"><div className="section-head split-head"><div><p className="eyebrow"><span></span> The student journey</p><h2>Many ways to <i>shine.</i></h2></div><p>Learning is not one straight line. It is a collection of moments, questions and discoveries that help each learner become more fully themselves.</p></div><div className="journey-grid">{journey.map(card => <article className={`journey-card ${card.color} reveal`} key={card.number}><div className="journey-art" aria-hidden="true"><span>J</span></div><div className="card-top"><span>{card.number}</span><span className="card-arrow">â†—</span></div><div><p className="card-kicker">{card.kicker}</p><h3>{card.title}</h3><p>{card.text}</p></div></article>)}</div><a className="button button-outline" href="/student-life">Enter the student journey <span>â†—</span></a></div></section>
    <FacilitiesSection />

    <section className="section values-section section-dark"><div className="shell values-grid"><div className="values-intro reveal"><p className="eyebrow eyebrow-light"><span></span> What guides us</p><h2>A strong start for a <i>bright</i> tomorrow.</h2><p>Our values are simple, human and designed to be lived every dayâ€”in classrooms, on the playground and in the way we care for one another.</p><div className="values-seal"><img src={logo} alt="Official Jigisha International School crest" /><span>Identity in<br /><strong>motion</strong></span></div><a className="text-link light-link" href="/why-jigisha">Why Jigisha <span>â†—</span></a></div><div className="pillars-grid">{pillars.map(([number, title, text]) => <div className="pillar reveal" key={number}><span>{number}</span><h3>{title}</h3><p>{text}</p></div>)}</div></div></section>

    <section className="section enquiry-section" id="enquiry"><div className="shell enquiry-grid"><div className="enquiry-copy reveal"><p className="eyebrow"><span></span> Begin a conversation</p><h2>Letâ€™s find the<br /><i>right next step.</i></h2><p>Tell us a little about your family and the school team will get back to you with the information you need.</p><div className="contact-note"><span className="note-icon">â†—</span><div><strong>Visit the school</strong><p>M-1 Jigisha, N-7, CIDCO<br />Chhatrapati Sambhajinagar<br />Maharashtra 431003, India</p></div></div></div><EnquiryForm /></div></section>

    <InitiativesSection />
    <AchievementsSection />
    <GallerySection />
    <NewsSection />

    <section className="section faq-section"><div className="shell faq-grid"><div className="faq-intro reveal"><p className="eyebrow"><span></span> Common questions</p><h2>Good to <i>know.</i></h2><p>Canâ€™t find what youâ€™re looking for? Our enquiry form is the quickest way to start a conversation.</p><a className="text-link" href="/contact">Ask us directly <span>â†—</span></a></div><div className="faq-list">{faqs.map(([question, answer], index) => <FaqItem key={question} question={question} answer={answer} openByDefault={index === 0} />)}</div></div></section>
    <ContactSection />

    <section className="closing-banner"><div className="shell closing-inner"><p className="eyebrow eyebrow-light"><span></span> Your next chapter</p><h2>Come curious.<br /><i>Leave inspired.</i></h2><a className="button button-orange" href="#enquiry">Start an enquiry <span>â†—</span></a></div></section>
  </main>
}

function Reveal({ children, className = '', delay = 0 }) {
  const elementRef = useRef(null)
  const isInView = useInView(elementRef, { once: true, margin: '-60px' })
  const reduceMotion = useReducedMotion()
  return <motion.div ref={elementRef} className={className} initial={reduceMotion ? false : { opacity: 0, y: 24 }} animate={isInView ? { opacity: 1, y: 0 } : undefined} transition={reduceMotion ? { duration: 0 } : { duration: 0.65, delay, ease: [0.22, 1, 0.36, 1] }}>{children}</motion.div>
}

function StatsSection() {
  return <section className="stats-section"><div className="shell stats-grid"><div className="stats-intro"><p className="eyebrow eyebrow-light"><span></span> A growing story</p><h2>Built for <i>whatâ€™s next.</i></h2><p>These markers will become a living snapshot of the Jigisha community as verified school information is confirmed.</p></div><div className="stats-list">{schoolStats.map((stat, index) => <Reveal className="stat-item" delay={index * 0.08} key={stat.label}><strong>{stat.value === null ? 'â€”' : <StatNumber value={stat.value} />}{stat.value !== null ? stat.suffix : ''}</strong><span>{stat.label}</span><small>{stat.value === null ? 'To be confirmed' : 'Jigisha snapshot'}</small></Reveal>)}</div></div></section>
}

function StatNumber({ value }) {
  const reduceMotion = useReducedMotion()
  return <motion.span initial={reduceMotion ? false : { opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ duration: .5 }}>{value}</motion.span>
}

function FacilitiesSection() {
  return <section className="section facilities-section"><div className="shell"><div className="section-head split-head"><div><p className="eyebrow"><span></span> Spaces for growth</p><h2>Room to <i>become.</i></h2></div><p>Good spaces invite good questions. These editable placeholders are ready for Jigisha campus photography when it becomes available.</p></div><div className="facilities-grid">{facilities.map((facility, index) => <Reveal className={`facility-card ${facility.tone}`} delay={index * .07} key={facility.number}><div className="facility-art"><span>{facility.number}</span><div className="facility-orbit"></div><div className="facility-orbit small"></div><b>J</b></div><div className="facility-copy"><h3>{facility.title}</h3><p>{facility.note}</p><a href="/gallery">View space <span>â†—</span></a></div></Reveal>)}</div></div></section>
}

function InitiativesSection() {
  return <section className="section initiatives-section section-dark"><div className="shell"><div className="section-head split-head"><div><p className="eyebrow eyebrow-light"><span></span> Initiatives & programmes</p><h2>Learning is <i>alive.</i></h2></div><p>Thoughtful programmes give students more ways to connect ideas, people and the world around them.</p></div><div className="initiative-grid">{initiatives.map((initiative, index) => <Reveal className={`initiative-card ${initiative.tone}`} delay={index * .08} key={initiative.title}><div className="initiative-graphic"><span>0{index + 1}</span><div></div></div><div><p className="card-kicker">{initiative.label}</p><h3>{initiative.title}</h3><p>{initiative.text}</p><a className="text-link light-link" href="/academics">Explore <span>â†—</span></a></div></Reveal>)}</div></div></section>
}

function AchievementsSection() {
  const hasAchievements = false
  return <section className="section achievements-section"><div className="shell achievements-grid"><div><p className="eyebrow"><span></span> Achievements</p><h2>Celebrate the <i>journey.</i></h2><p className="muted-copy">Verified Jigisha achievements and milestones will be added here as the school community begins to create them.</p><a className="text-link" href="/achievements">View achievements <span>â†—</span></a></div><div className="achievement-carousel" aria-label="Jigisha achievements"><div className="achievement-carousel-head"><span>{hasAchievements ? 'Verified milestones' : '0 verified milestones'}</span><div><button type="button" disabled={!hasAchievements} aria-label="Previous achievement">â€¹</button><button type="button" disabled={!hasAchievements} aria-label="Next achievement">â€º</button></div></div><div className="achievement-empty"><span className="achievement-star">âœ¦</span><span className="eyebrow"><span></span> Record in progress</span><h3>Every first step<br /><i>counts.</i></h3><p>A considered space for awards, learner milestones and community moments.</p><div className="achievement-progress"><span></span></div></div></div></div></section>
}

function GallerySection() {
  const [active, setActive] = useState(null)
  useEffect(() => {
    if (active === null) return undefined
    const onKeyDown = event => {
      if (event.key === 'Escape') setActive(null)
      if (event.key === 'ArrowRight') setActive(index => (index + 1) % galleryPlaceholders.length)
      if (event.key === 'ArrowLeft') setActive(index => (index - 1 + galleryPlaceholders.length) % galleryPlaceholders.length)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [active])
  const current = active === null ? null : galleryPlaceholders[active]
  return <section className="section gallery-section section-paper"><div className="shell"><div className="section-head split-head"><div><p className="eyebrow"><span></span> Gallery</p><h2>See the <i>possibility.</i></h2></div><p>Replace these considered placeholders with Jigisha campus and community photography without changing the gallery architecture.</p></div><div className="gallery-grid">{galleryPlaceholders.map((item, index) => <Reveal className={`gallery-tile ${item.tone} gallery-${index + 1}`} delay={index * .05} key={item.title}><button className="gallery-trigger" onClick={() => setActive(index)} aria-label={`Open ${item.category} gallery image`}><div className="gallery-pattern"><span>J</span></div><div className="gallery-caption"><small>{item.category}</small><strong>{item.title}</strong><span>â†—</span></div></button></Reveal>)}</div><a className="button button-outline" href="/gallery">Open the gallery <span>â†—</span></a></div>{current ? <AnimatePresence><motion.div className="lightbox" role="dialog" aria-modal="true" aria-label={`${current.category} gallery image`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><button className="lightbox-close" onClick={() => setActive(null)} aria-label="Close gallery">Ã—</button><button className="lightbox-nav lightbox-prev" onClick={() => setActive(index => (index - 1 + galleryPlaceholders.length) % galleryPlaceholders.length)} aria-label="Previous image">â€¹</button><div className={`lightbox-art ${current.tone}`}><div className="gallery-pattern"><span>J</span></div><div className="lightbox-copy"><small>{current.category} / {String(active + 1).padStart(2, '0')}</small><h3>{current.title}</h3><p>Image placeholder ready for Jigisha photography.</p></div></div><button className="lightbox-nav lightbox-next" onClick={() => setActive(index => (index + 1) % galleryPlaceholders.length)} aria-label="Next image">â€º</button></motion.div></AnimatePresence> : null}</section>
}

function NewsSection() {
  const [items, setItems] = useState(newsPlaceholders)
  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL
    if (!apiUrl) return undefined
    fetch(`${apiUrl}/news`).then(response => response.ok ? response.json() : Promise.reject()).then(payload => { if (payload.items?.length) setItems(payload.items) }).catch(() => undefined)
    return undefined
  }, [])
  return <section className="section news-section"><div className="shell"><div className="section-head split-head"><div><p className="eyebrow"><span></span> News & events</p><h2>From the <i>community.</i></h2></div><p>Updates, announcements and stories will live here as the Jigisha school calendar develops.</p></div><div className="news-grid">{items.map((item, index) => <Reveal className="news-card" delay={index * .07} key={item.title}><div className={`news-art news-art-${(index % 3) + 1}`}>{item.image ? <img src={item.image} alt="" loading="lazy" /> : null}<span>{String(index + 1).padStart(2, '0')}</span><b>J</b></div><div className="news-copy"><div><small>{item.date}</small><small>{item.category}</small></div><h3>{item.title}</h3><p>{item.text || item.description}</p><a href="/news">Read more <span>â†—</span></a></div></Reveal>)}</div></div></section>
}

function ContactSection() {
  return <section className="contact-section section-dark"><div className="shell contact-grid"><div><p className="eyebrow eyebrow-light"><span></span> Visit Jigisha</p><h2>Find your way<br /><i>to us.</i></h2><p className="contact-lead">Jigisha International School<br />M-1 Jigisha, N-7, CIDCO<br />Chhatrapati Sambhajinagar<br />Maharashtra 431003, India</p><a className="button button-orange" href="/contact">Contact the school <span>â†—</span></a></div><div className="map-card"><div className="map-grid-lines"></div><div className="map-pin"><span>J</span></div><div className="map-label">N-7 Â· CIDCO<br /><strong>Jigisha International School</strong></div><span className="map-caption">Map integration ready</span></div></div></section>
}

function ProgramCard({ number, title, text, tone }) { return <article className={`program-card ${tone} reveal`}><div className="program-graphic"><span>{number}</span><div className="graphic-shape"></div></div><div className="program-body"><h3>{title}</h3><p>{text}</p><a href="/academics" aria-label={`Learn more about ${title}`}>Explore <span>â†—</span></a></div></article> }

function EnquiryForm() {
  const [status, setStatus] = useState('idle')
  const [form, setForm] = useState({ parent: '', student: '', email: '', mobile: '', grade: '', message: '' })
  const update = event => setForm({ ...form, [event.target.name]: event.target.value })
  const submit = async event => {
    event.preventDefault()
    setStatus('loading')
    const apiUrl = import.meta.env.VITE_API_URL
    if (!apiUrl) { setStatus('success'); return }
    try {
      const response = await fetch(`${apiUrl}/enquiries`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
      if (!response.ok) throw new Error('Unable to submit enquiry')
      setStatus('success')
    } catch {
      setStatus('error')
    }
  }
  if (status === 'success') return <div className="form-success reveal"><span className="success-mark">âœ“</span><p className="eyebrow"><span></span> Thank you</p><h3>Your enquiry is on its way.</h3><p>Weâ€™ve recorded your interest. The school team will be in touch with the information you need.</p><button className="text-link" onClick={() => { setStatus('idle'); setForm({ parent: '', student: '', email: '', mobile: '', grade: '', message: '' }) }}>Send another enquiry <span>â†—</span></button></div>
  return <form className="enquiry-form reveal delay-one" onSubmit={submit}><div className="form-heading"><span>Enquiry form</span><small>All fields marked * are required</small></div>{status === 'error' ? <p className="form-error" role="alert">We couldnâ€™t send that just now. Please try again or contact the school directly.</p> : null}<div className="form-row"><label>Parent / guardian name *<input required name="parent" value={form.parent} onChange={update} placeholder="Your full name" /></label><label>Student name *<input required name="student" value={form.student} onChange={update} placeholder="Studentâ€™s full name" /></label></div><div className="form-row"><label>Email address *<input required type="email" name="email" value={form.email} onChange={update} placeholder="you@example.com" /></label><label>Mobile number *<input required name="mobile" value={form.mobile} onChange={update} placeholder="Your mobile number" /></label></div><div className="form-row"><label>Grade / standard<select required name="grade" value={form.grade} onChange={update}><option value="">Select a grade</option><option>Early years</option><option>Primary school</option><option>Middle school</option><option>Secondary school</option><option>Not sure yet</option></select></label><label>What can we help with?<input name="message" value={form.message} onChange={update} placeholder="Tell us a little more" /></label></div><div className="form-footer"><p>By submitting, you agree that Jigisha may use these details to respond to your enquiry.</p><button className="button button-blue" type="submit" disabled={status === 'loading'}>{status === 'loading' ? 'Sendingâ€¦' : 'Send enquiry'} <span>â†—</span></button></div></form>
}

function FaqItem({ question, answer, openByDefault }) {
  const [open, setOpen] = useState(openByDefault)
  return <div className={`faq-item ${open ? 'open' : ''}`}><button onClick={() => setOpen(!open)} aria-expanded={open}><span>{question}</span><b>{open ? 'âˆ’' : '+'}</b></button><AnimatePresence initial={false}>{open ? <motion.div className="faq-answer-motion" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: .25 }}><p>{answer}</p></motion.div> : null}</AnimatePresence></div>
}

function InnerPage({ path }) {
  const config = pageConfig(path)
  return <main className="inner-page"><section className="inner-hero section-dark"><div className="shell inner-hero-grid"><div><p className="eyebrow eyebrow-light"><span></span> Jigisha International School</p><h1>{config.title}<br /><i>{config.italic}</i></h1><p>{config.intro}</p></div><div className="inner-emblem"><img src={logo} alt="Jigisha International School official crest" loading="lazy" /><span>Establishing a place<br />to learn & belong</span></div></div></section><section className="section page-content"><div className="shell page-content-grid"><aside><p className="eyebrow"><span></span> Explore</p><nav>{['/about', '/academics', '/why-jigisha', '/admissions', '/student-life', '/gallery', '/achievements', '/news', '/contact'].map(href => <a className={path === href ? 'active' : ''} href={href} key={href}>{pageTitle(href)} <span>â†—</span></a>)}</nav></aside><div className="page-main"><div className="page-visual"><div className="page-visual-rings"></div><img src={logo} alt="Official Jigisha International School crest" loading="lazy" /><span>{pageTitle(path)} / Jigisha</span></div>{config.blocks.map((block, index) => <div className="content-block reveal" key={index}>{block.type === 'heading' ? <h2>{block.text}</h2> : block.type === 'list' ? <div className="content-list">{block.items.map(item => <div key={item[0]}><span>{item[0]}</span><div><h3>{item[1]}</h3><p>{item[2]}</p></div></div>)}</div> : <p>{block.text}</p>}</div>)}{path === '/admissions' || path === '/contact' ? <div className="page-cta"><h3>Ready to start a conversation?</h3><p>Share your details and weâ€™ll help with the next step.</p><a className="button button-blue" href="/#enquiry">Open enquiry form <span>â†—</span></a></div> : null}</div></div></section></main>
}

function Footer() { return <footer className="site-footer"><div className="shell footer-top"><div className="footer-brand"><a className="brand brand-footer" href="/"><span className="brand-mark"><img src={logo} alt="" /></span><span className="brand-copy"><strong>Jigisha</strong><em>International School</em></span></a><p>A place to learn with curiosity, grow with confidence and belong with purpose.</p></div><div className="footer-column"><h4>Explore</h4><a href="/about">About school</a><a href="/academics">Academics</a><a href="/why-jigisha">Why Jigisha</a><a href="/admissions">Admissions</a></div><div className="footer-column"><h4>Discover</h4><a href="/student-life">Student life</a><a href="/gallery">Gallery</a><a href="/achievements">Achievements</a><a href="/news">News & events</a></div><div className="footer-column footer-address"><h4>Find us</h4><p>M-1 Jigisha, N-7, CIDCO<br />Chhatrapati Sambhajinagar<br />Maharashtra 431003, India</p><a href="/contact">Contact the school <span>â†—</span></a></div></div><div className="shell footer-bottom"><span>Â© {new Date().getFullYear()} Jigisha International School</span><span>Made for curious minds <b>âœ¦</b></span><span><a href="/">Privacy</a> Â· <a href="/">Terms</a></span></div></footer> }

function pageTitle(path) { return ({ '/about': 'About', '/academics': 'Academics', '/why-jigisha': 'Why Jigisha', '/admissions': 'Admissions', '/student-life': 'Student life', '/gallery': 'Gallery', '/achievements': 'Achievements', '/news': 'News', '/contact': 'Contact' })[path] || 'Jigisha' }
function pageConfig(path) {
  const base = { '/about': { title: 'A school shaped', italic: 'around possibility.', intro: 'A thoughtful beginning for learners, families and a community growing together.', blocks: [{ type: 'heading', text: 'Learning is more than a timetable.' }, { text: 'Jigisha International School is being built as a welcoming space for questions, confidence and connection. The schoolâ€™s identity is rooted in the belief that education should help young people understand the worldâ€”and their place in it.' }, { type: 'list', items: pillars.map(([n, t, x]) => [n, t, x]) }] }, '/academics': { title: 'Make learning', italic: 'matter.', intro: 'An approach that values strong foundations, active thinking and the joy of finding things out.', blocks: [{ type: 'heading', text: 'The classroom is a starting point.' }, { text: 'Our academic approach is designed to keep learners engaged with ideas, people and the world around them. Detailed curriculum and grade information will be shared by the school team as it is confirmed.' }, { type: 'list', items: [['01', 'Foundations', 'Clear concepts, good questions and a steady sense of progress.'], ['02', 'Application', 'Learning that connects to real situations and meaningful problems.'], ['03', 'Expression', 'Multiple ways to explain, make, present and understand.']] }] }, '/why-jigisha': { title: 'The Jigisha', italic: 'difference.', intro: 'A human-scale idea of school: high expectations, open minds and a strong sense of belonging.', blocks: [{ type: 'heading', text: 'The best learning feels personal.' }, { text: 'We are creating an environment where learners are known, supported and encouraged to take meaningful responsibility. Our values are lived through the everyday details of school life.' }, { type: 'list', items: journey.slice(0, 4).map(card => [card.number, card.title, card.text]) }] }, '/admissions': { title: 'Your next step', italic: 'starts here.', intro: 'Tell us what you need to know and the school team will help you move forward with clarity.', blocks: [{ type: 'heading', text: 'A clear beginning matters.' }, { text: 'Admission availability, grade details and required documents are best confirmed directly with the school. Use the enquiry form to start a conversation with the team.' }, { type: 'list', items: [['01', 'Send an enquiry', 'Share a few details about your family and preferred grade.'], ['02', 'Speak with the school', 'Receive current information and guidance for your situation.'], ['03', 'Visit and decide', 'Take the next step when you have the clarity you need.']] }] }, '/student-life': { title: 'A full life', italic: 'at school.', intro: 'The moments between lessons matter too: friendships, movement, creativity and discovery.', blocks: [{ type: 'heading', text: 'There is more than one way to learn.' }, { text: 'Student life at Jigisha is designed to make space for collaboration, expression and active wellbeing. As programmes are confirmed, this space will grow with the school community.' }, { type: 'list', items: journey.map(card => [card.number, card.title, card.text]) }] }, '/gallery': { title: 'See Jigisha', italic: 'in the making.', intro: 'A visual journal of the spaces, people and moments that make a school feel like a community.', blocks: [{ type: 'heading', text: 'Our story will be pictured here.' }, { text: 'School and campus photography will be added as the Jigisha image library develops. Until then, our official crest and visual language hold the place for the stories to come.' }, { type: 'list', items: [['01', 'Campus', 'The places where everyday learning happens.'], ['02', 'Community', 'The people and moments that bring school life to colour.'], ['03', 'Celebration', 'The milestones, events and achievements we share.']] }] }, '/achievements': { title: 'Every step', italic: 'counts.', intro: 'We will celebrate the milestones and moments that are meaningful to the Jigisha community.', blocks: [{ type: 'heading', text: 'A record in progress.' }, { text: 'Verified achievements, awards and school milestones will be published here as they become available. We will always keep this record accurate and useful for families.' }, { type: 'list', items: [['01', 'Learner growth', 'Recognising progress, effort and thoughtful contribution.'], ['02', 'Community moments', 'Celebrating the shared experiences that bring us together.']] }] }, '/news': { title: 'Whatâ€™s happening', italic: 'at Jigisha.', intro: 'Notes, announcements and stories from a school community taking shape.', blocks: [{ type: 'heading', text: 'The latest will be shared here.' }, { text: 'News and event updates will be published in this space once the schoolâ€™s content calendar is active. For current information, please contact the school directly.' }, { type: 'list', items: [['01', 'School updates', 'Important information for families and the wider community.'], ['02', 'Community stories', 'Small moments and big ideas from life at Jigisha.']] }] }, '/contact': { title: 'Letâ€™s talk', italic: 'about school.', intro: 'Weâ€™re here to help with the questions that matter to your family.', blocks: [{ type: 'heading', text: 'Find us in N-7, CIDCO.' }, { text: 'Jigisha International School\nM-1 Jigisha, N-7, CIDCO\nChhatrapati Sambhajinagar, Maharashtra 431003, India' }, { type: 'list', items: [['01', 'Enquiries', 'Use the enquiry form to share your questions and preferred contact details.'], ['02', 'School visit', 'Contact the school team to ask about the right time to visit.']] }] } }
  return base[path] || base['/about']
}

export default App


