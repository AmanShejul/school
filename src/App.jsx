import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion, useInView, useReducedMotion } from 'framer-motion'
import { facilities, galleryVisuals, imageAssets, initiatives, newsItems, schoolStats } from './data/siteData'
import { adminLogin, adminLogout, deleteAdminEnquiry, getAdminEnquiries, getAdminEnquiry, getAdminStats, getNews, submitAdmissionEnquiry, submitContact, submitEnquiry, updateAdminEnquiry } from './services/api'

const logo = imageAssets.logo
const heroImage = imageAssets.heroImage

function Icon({ name, size = 16, strokeWidth = 1.8 }) {
  const paths = {
    'arrow-up-right': <><path d="M5 19 19 5" /><path d="M8 5h11v11" /></>,
    'chevron-down': <path d="m4 7 8 8 8-8" />,
    'chevron-left': <path d="m15 18-6-6 6-6" />,
    'chevron-right': <path d="m9 18 6-6-6-6" />,
    close: <><path d="M5 5 19 19" /><path d="M19 5 5 19" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    sparkle: <><path d="m12 3-1.4 5.6L5 10l5.6 1.4L12 17l1.4-5.6L19 10l-5.6-1.4L12 3Z" /><path d="M19 16v5M21.5 18.5h-5" /></>,
    pin: <><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></>,
    book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5v-16Z" /><path d="M4 18.5A2.5 2.5 0 0 1 6.5 16H20" /></>,
    compass: <><circle cx="12" cy="12" r="9" /><path d="m15.5 8.5-2.2 4.8-4.8 2.2 2.2-4.8 4.8-2.2Z" /></>,
    flask: <><path d="M9 3h6M10 3v5l-5.2 8.8A3 3 0 0 0 7.4 21h9.2a3 3 0 0 0 2.6-4.2L14 8V3" /><path d="M7.4 16h9.2" /></>,
    activity: <path d="M3 12h4l2-7 4 14 2-7h6" />,
    palette: <><path d="M12 3a9 9 0 0 0 0 18h1.2a1.8 1.8 0 0 0 1.3-3.1c-.8-.8-.2-2.2.9-2.2H17a4 4 0 0 0 4-4C21 6.9 17 3 12 3Z" /><circle cx="7.5" cy="11" r=".7" fill="currentColor" /><circle cx="9" cy="7.5" r=".7" fill="currentColor" /><circle cx="13" cy="6.5" r=".7" fill="currentColor" /></>,
    building: <><path d="M4 21V5l8-3 8 3v16" /><path d="M8 9h1M8 13h1M8 17h1M15 9h1M15 13h1M15 17h1M11 21v-4h2v4" /></>,
  }
  return <svg className={`icon icon-${name}`} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

const navItems = [
  { label: 'About', href: '/about', children: ['About school', 'Vision & mission', "Principal's message"] },
  { label: 'Academics', href: '/academics', children: ['Curriculum', 'Teaching approach', 'Activities'] },
  { label: 'Why Jigisha', href: '/why-jigisha', children: ['Our difference', 'School values', 'Learning spaces'] },
  { label: 'Admissions', href: '/admissions', children: ['Admission process', 'Required documents', { label: 'Enquiry', href: '/admissions#enquiry-form' }] },
  { label: 'Student life', href: '/student-life', children: ['Events', 'Sports', 'Arts & culture'] },
  { label: 'Explore', href: '/gallery', children: [{ label: 'Gallery', href: '/gallery' }, { label: 'Achievements', href: '/achievements' }, { label: 'News', href: '/news' }] },
]

const journey = [
  { number: '01', kicker: 'Think deeply', title: 'Academic excellence', text: 'A thoughtful space for questions, clarity and confidence.', color: 'blue' },
  { number: '02', kicker: 'Make boldly', title: 'Creativity', text: 'Room to explore ideas through art, design, performance and making.', color: 'orange' },
  { number: '03', kicker: 'Move freely', title: 'Sports & wellbeing', text: 'A place for movement, teamwork and a healthy rhythm.', color: 'green' },
  { number: '04', kicker: 'Grow together', title: 'Values', text: 'The everyday habits of respect, responsibility and belonging.', color: 'navy' },
  { number: '05', kicker: 'Look ahead', title: 'Innovation', text: 'Curiosity and practical confidence for a changing world.', color: 'lime' },
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

function getLocation() {
  return { path: window.location.pathname || '/', hash: window.location.hash }
}

function anchorFor(label) {
  return label.toLowerCase().trim().replace(/\s+/g, '-')
}

function App() {
  const [location, setLocation] = useState(getLocation)
  const [menuOpen, setMenuOpen] = useState(false)
  const [openDropdown, setOpenDropdown] = useState(null)
  const [scrolled, setScrolled] = useState(false)

  const navigate = (to) => {
    const next = new URL(to, window.location.origin)
    const nextUrl = `${next.pathname}${next.search}${next.hash}`
    window.history.pushState({}, '', nextUrl)
    setLocation({ path: next.pathname || '/', hash: next.hash })
    setMenuOpen(false)
    setOpenDropdown(null)
    window.requestAnimationFrame(() => {
      if (next.hash) document.getElementById(next.hash.slice(1))?.scrollIntoView({ behavior: 'smooth' })
      else window.scrollTo({ top: 0, behavior: 'smooth' })
    })
  }

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    const onPopState = () => {
      setLocation(getLocation())
      setMenuOpen(false)
      setOpenDropdown(null)
    }
    window.addEventListener('popstate', onPopState)
    window.addEventListener('hashchange', onPopState)
    return () => {
      window.removeEventListener('popstate', onPopState)
      window.removeEventListener('hashchange', onPopState)
    }
  }, [])

  useEffect(() => {
    document.title = location.path === '/' ? 'Jigisha International School' : `${pageTitle(location.path)} · Jigisha International School`
    if (location.hash) {
      window.requestAnimationFrame(() => document.getElementById(location.hash.slice(1))?.scrollIntoView({ behavior: 'smooth' }))
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }, [location])

  if (location.path === '/admin/login') return <AdminLoginPage navigate={navigate} />
  if (location.path === '/admin') return <AdminDashboard navigate={navigate} />

  return <>
    <div className="utility-bar"><div className="shell utility-inner"><span>JIGISHA INTERNATIONAL SCHOOL</span><span className="utility-location">N-7, CIDCO · Chhatrapati Sambhajinagar</span><a href="/#enquiry" onClick={event => { event.preventDefault(); navigate('/#enquiry') }}>Start an enquiry <Icon name="arrow-up-right" size={14} /></a></div></div>
    <header className={`site-header ${scrolled ? 'is-scrolled' : ''}`}>
      <div className="shell nav-inner">
        <a className="brand" href="/" onClick={event => { event.preventDefault(); navigate('/') }} aria-label="Jigisha International School home"><span className="brand-mark"><img src={logo} alt="" /></span><span className="brand-copy"><strong>Jigisha</strong><em>International School</em></span></a>
        <nav className={`desktop-nav ${menuOpen ? 'mobile-open' : ''}`} aria-label="Primary navigation">
          <a href="/" className="nav-home" onClick={event => { event.preventDefault(); navigate('/') }}>Home</a>
          {navItems.map(item => <div className={`nav-dropdown ${openDropdown === item.label ? 'dropdown-open' : ''}`} key={item.label}>
            <div className="nav-parent"><a href={item.href} onClick={event => { event.preventDefault(); navigate(item.href) }}>{item.label}<Icon name="chevron-down" size={13} /></a><button type="button" className="dropdown-toggle" aria-label={`Toggle ${item.label} menu`} aria-expanded={openDropdown === item.label} onClick={() => setOpenDropdown(openDropdown === item.label ? null : item.label)}><Icon name="chevron-down" size={13} /></button></div>
            <div className="dropdown-menu">{item.children.map(child => { const childHref = typeof child === 'string' ? `${item.href}#${anchorFor(child)}` : child.href; const childLabel = typeof child === 'string' ? child : child.label; return <a key={childLabel} href={childHref} onClick={event => { event.preventDefault(); navigate(childHref) }}>{childLabel}</a> })}</div>
          </div>)}
          <a className="nav-contact" href="/contact" onClick={event => { event.preventDefault(); navigate('/contact') }}>Contact <Icon name="arrow-up-right" size={14} /></a>
        </nav>
        <a className="button button-small nav-cta" href="/#enquiry" onClick={event => { event.preventDefault(); navigate('/#enquiry') }}>Enquire now <Icon name="arrow-up-right" size={14} /></a>
        <button type="button" className={`menu-toggle ${menuOpen ? 'open' : ''}`} onClick={() => setMenuOpen(!menuOpen)} aria-label={menuOpen ? 'Close navigation' : 'Open navigation'} aria-expanded={menuOpen}><span></span><span></span></button>
      </div>
    </header>
    {location.path === '/' ? <Home /> : <InnerPage path={location.path} />}
    <Footer />
  </>
}

function AdminLoginPage({ navigate }) {
  const [form, setForm] = useState({ email: '', password: '' })
  const [status, setStatus] = useState('idle')
  const update = event => setForm(current => ({ ...current, [event.target.name]: event.target.value }))
  const submit = async event => {
    event.preventDefault()
    if (!form.email.trim() || !form.password) { setStatus('error'); return }
    setStatus('loading')
    try { await adminLogin({ email: form.email.trim(), password: form.password }); navigate('/admin') } catch { setStatus('error') }
  }
  useEffect(() => { document.title = 'Admin login · Jigisha International School' }, [])
  return <main className="admin-page admin-login-page"><div className="admin-login-card"><a className="admin-brand" href="/" onClick={event => { event.preventDefault(); navigate('/') }}><span className="admin-brand-mark"><img src={logo} alt="" /></span><span><strong>Jigisha</strong><small>International School</small></span></a><p className="admin-eyebrow">Administration</p><h1>Welcome back.</h1><p className="admin-muted">Sign in to manage school enquiries.</p><form className="admin-login-form" onSubmit={submit} noValidate>{status === 'error' ? <p className="admin-alert" role="alert">Unable to sign in. Check your details and try again.</p> : null}<label>Email address<input type="email" name="email" value={form.email} onChange={update} autoComplete="username" required /></label><label>Password<input type="password" name="password" value={form.password} onChange={update} autoComplete="current-password" required /></label><button className="admin-primary-button" type="submit" disabled={status === 'loading'}>{status === 'loading' ? 'Signing in…' : 'Sign in'} <Icon name="arrow-up-right" size={15} /></button></form><a className="admin-back-link" href="/" onClick={event => { event.preventDefault(); navigate('/') }}>Back to public website</a></div></main>
}

function AdminDashboard({ navigate }) {
  const [stats, setStats] = useState(null)
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState({ search: '', status: '', grade: '' })
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [nextStats, nextEnquiries] = await Promise.all([getAdminStats(), getAdminEnquiries(filters)])
      setStats(nextStats)
      setItems(nextEnquiries.items || [])
      setTotal(nextEnquiries.total || 0)
    } catch (requestError) {
      if (requestError.status === 401) navigate('/admin/login')
      else setError('We couldn’t load the enquiry records. Please try again.')
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [filters.search, filters.status, filters.grade])
  useEffect(() => { document.title = 'Administration · Jigisha International School' }, [])
  useEffect(() => { if (!toast) return undefined; const timer = window.setTimeout(() => setToast(''), 2800); return () => window.clearTimeout(timer) }, [toast])

  const updateFilter = event => setFilters(current => ({ ...current, [event.target.name]: event.target.value }))
  const openDetail = async id => {
    try { setSelected(await getAdminEnquiry(id)) } catch (requestError) { if (requestError.status === 401) navigate('/admin/login'); else setError('Unable to open this enquiry.') }
  }
  const changeStatus = async (id, status) => {
    try { await updateAdminEnquiry(id, { status }); setToast('Enquiry status updated.'); await load(); if (selected?.id === id) setSelected(current => ({ ...current, status })) } catch (requestError) { if (requestError.status === 401) navigate('/admin/login'); else setError('Unable to update this enquiry.') }
  }
  const remove = async id => {
    if (!window.confirm('Delete this enquiry permanently?')) return
    try { await deleteAdminEnquiry(id); setSelected(current => current?.id === id ? null : current); setToast('Enquiry deleted.'); await load() } catch (requestError) { if (requestError.status === 401) navigate('/admin/login'); else setError('Unable to delete this enquiry.') }
  }
  const logout = async () => { try { await adminLogout() } finally { navigate('/admin/login') } }

  return <main className="admin-page"><div className="admin-shell"><header className="admin-header"><div className="admin-header-brand"><span className="admin-brand-mark"><img src={logo} alt="" /></span><div><strong>Jigisha International School</strong><span>Administration</span></div></div><div className="admin-header-actions"><a href="/" onClick={event => { event.preventDefault(); navigate('/') }}>View website</a><button type="button" onClick={logout}>Log out</button></div></header><section className="admin-welcome"><div><p className="admin-eyebrow">School administration</p><h1>Enquiries</h1><p className="admin-muted">Review, follow up and keep every family conversation moving.</p></div><button type="button" className="admin-refresh" onClick={load}>Refresh <Icon name="arrow-up-right" size={14} /></button></section>{stats ? <div className="admin-stats-grid"><AdminStat label="Total enquiries" value={stats.total_enquiries} tone="blue" /><AdminStat label="New enquiries" value={stats.new_enquiries} tone="orange" /><AdminStat label="Contacted" value={stats.contacted_enquiries} tone="green" /><AdminStat label="Closed" value={stats.closed_enquiries} tone="navy" /></div> : null}<section className="admin-panel"><div className="admin-panel-head"><div><h2>Enquiry records</h2><span>{total} {total === 1 ? 'record' : 'records'}</span></div><div className="admin-filters"><label className="admin-search"><span className="sr-only">Search enquiries</span><input name="search" value={filters.search} onChange={updateFilter} placeholder="Search parent, student, email or mobile" /></label><label><span className="sr-only">Filter by grade</span><input name="grade" value={filters.grade} onChange={updateFilter} placeholder="Grade" /></label><label><span className="sr-only">Filter by status</span><select name="status" value={filters.status} onChange={updateFilter}><option value="">All statuses</option><option value="new">New</option><option value="contacted">Contacted</option><option value="closed">Closed</option></select></label></div></div>{error ? <p className="admin-alert" role="alert">{error}</p> : null}{loading ? <div className="admin-empty">Loading enquiries…</div> : items.length === 0 ? <div className="admin-empty"><strong>No enquiries yet.</strong><span>New parent enquiries will appear here.</span></div> : <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Parent</th><th>Student</th><th>Grade</th><th>Email</th><th>Mobile</th><th>Status</th><th>Submitted</th><th>Actions</th></tr></thead><tbody>{items.map(item => <tr key={item.id}><td data-label="Parent"><strong>{item.parent}</strong></td><td data-label="Student">{item.student}</td><td data-label="Grade">{item.grade}</td><td data-label="Email">{item.email}</td><td data-label="Mobile">{item.mobile}</td><td data-label="Status"><select className={`admin-status-select status-${item.status}`} value={item.status} onChange={event => changeStatus(item.id, event.target.value)} aria-label={`Change status for ${item.parent}`}><option value="new">New</option><option value="contacted">Contacted</option><option value="closed">Closed</option></select></td><td data-label="Submitted">{formatAdminDate(item.created_at)}</td><td data-label="Actions"><div className="admin-row-actions"><button type="button" onClick={() => openDetail(item.id)}>View</button><button type="button" className="admin-delete" onClick={() => remove(item.id)}>Delete</button></div></td></tr>)}</tbody></table></div>}</section></div>{toast ? <div className="admin-toast" role="status">{toast}</div> : null}{selected ? <div className="admin-modal-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setSelected(null) }}><section className="admin-detail" role="dialog" aria-modal="true" aria-labelledby="admin-detail-title"><button type="button" className="admin-modal-close" onClick={() => setSelected(null)} aria-label="Close enquiry details"><Icon name="close" size={21} /></button><p className="admin-eyebrow">Enquiry #{selected.id}</p><h2 id="admin-detail-title">{selected.parent}</h2><div className="admin-detail-status"><span>Current status</span><select className={`admin-status-select status-${selected.status}`} value={selected.status} onChange={event => changeStatus(selected.id, event.target.value)}><option value="new">New</option><option value="contacted">Contacted</option><option value="closed">Closed</option></select></div><dl><div><dt>Student</dt><dd>{selected.student}</dd></div><div><dt>Email</dt><dd>{selected.email}</dd></div><div><dt>Mobile</dt><dd>{selected.mobile}</dd></div><div><dt>Grade</dt><dd>{selected.grade}</dd></div><div><dt>Submitted</dt><dd>{formatAdminDate(selected.created_at)}</dd></div><div className="admin-detail-message"><dt>Message</dt><dd>{selected.message || 'No message provided.'}</dd></div></dl><button type="button" className="admin-danger-button" onClick={() => remove(selected.id)}>Delete enquiry</button></section></div> : null}</main>
}

function AdminStat({ label, value, tone }) {
  return <div className={`admin-stat admin-stat-${tone}`}><span>{label}</span><strong>{value ?? '—'}</strong><small>Verified database total</small></div>
}

function formatAdminDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

function Home() {
  return <main>
    <section className="hero section-dark">
      <div className="hero-orbit orbit-one"></div><div className="hero-orbit orbit-two"></div>
      <div className="shell hero-grid">
        <div className="hero-copy reveal"><p className="eyebrow eyebrow-light"><span></span> School for the whole child</p><h1>Learning today.<br /><i>Leading</i><br /> tomorrow.</h1><p className="hero-intro">A welcoming learning community in Chhatrapati Sambhajinagar, where curiosity becomes confidence and every learner is encouraged to find their own way forward.</p><div className="hero-actions"><a className="button button-orange" href="#enquiry">Explore our school <Icon name="arrow-up-right" size={15} /></a><a className="text-link light-link" href="/admissions">Admissions <Icon name="arrow-up-right" size={15} /></a></div></div>
        <div className="hero-visual reveal delay-one"><div className={`hero-frame ${heroImage ? 'has-photo' : ''}`}><div className="frame-accent"></div><div className="frame-inner"><span className="frame-label">Jigisha / 01</span><img src={heroImage || logo} alt={heroImage ? 'Jigisha International School building' : 'Jigisha International School official crest'} /><div className="frame-note">A place to<br /><strong>belong & grow</strong></div></div></div><div className="hero-stamp"><strong>J</strong><span>Chhatrapati<br />Sambhajinagar</span></div></div>
      </div>
      <div className="hero-footer shell"><span>Scroll to explore</span><span className="scroll-line"></span><span>01 / 04</span></div>
    </section>

    <section className="quick-actions"><div className="shell quick-grid"><a href="/about"><span className="action-number">01</span><strong>Discover Jigisha</strong><Icon name="arrow-up-right" size={16} /></a><a href="/academics"><span className="action-number">02</span><strong>Learning at Jigisha</strong><Icon name="arrow-up-right" size={16} /></a><a href="/admissions"><span className="action-number">03</span><strong>Join our community</strong><Icon name="arrow-up-right" size={16} /></a><a href="/contact"><span className="action-number">04</span><strong>Find us</strong><Icon name="arrow-up-right" size={16} /></a></div></section>

    <section className="section intro-section"><div className="shell intro-grid"><div className="intro-aside reveal"><p className="eyebrow"><span></span> About Jigisha</p><p className="aside-number">01<span>/</span>04</p></div><div className="intro-content reveal delay-one"><h2>Where learning meets <i>curiosity,</i> creativity and character.</h2><p>Jigisha International School is a place for thoughtful beginnings and brave next steps. Our visual identity speaks of energy, movement and possibility; our school experience is being shaped around the same promise.</p><a className="text-link" href="/about">Read our story <Icon name="arrow-up-right" size={15} /></a></div><div className="intro-art reveal delay-two"><div className="art-disc intro-photo"><img src={imageAssets.heroImage} alt="Jigisha International School building" loading="lazy" /></div><span className="art-caption">Our school / Jigisha International School</span></div></div></section>
    <StatsSection />

    <section className="section journey-section section-paper"><div className="shell"><div className="section-head split-head"><div><p className="eyebrow"><span></span> The student journey</p><h2>Many ways to <i>shine.</i></h2></div><p>Learning is not one straight line. It is a collection of moments, questions and discoveries that help each learner become more fully themselves.</p></div><div className="journey-grid">{journey.map(card => <article className={`journey-card ${card.color} reveal`} key={card.number}><div className="journey-art" aria-hidden="true"><span>J</span></div><div className="card-top"><span>{card.number}</span><Icon name="arrow-up-right" size={17} /></div><div><p className="card-kicker">{card.kicker}</p><h3>{card.title}</h3><p>{card.text}</p></div></article>)}</div><a className="button button-outline" href="/student-life">Enter the student journey <Icon name="arrow-up-right" size={15} /></a></div></section>
    <FacilitiesSection />

    <section className="section values-section section-dark"><div className="shell values-grid"><div className="values-intro reveal"><p className="eyebrow eyebrow-light"><span></span> What guides us</p><h2>A strong start for a <i>bright</i> tomorrow.</h2><p>Our values are simple, human and designed to be lived every day — in classrooms, on the playground and in the way we care for one another.</p><div className="values-seal"><img src={logo} alt="Official Jigisha International School crest" /><span>Identity in<br /><strong>motion</strong></span></div><a className="text-link light-link" href="/why-jigisha">Why Jigisha <Icon name="arrow-up-right" size={15} /></a></div><div className="pillars-grid">{pillars.map(([number, title, text]) => <div className="pillar reveal" key={number}><span>{number}</span><h3>{title}</h3><p>{text}</p></div>)}</div></div></section>

    <section className="section enquiry-section" id="enquiry"><div className="shell enquiry-grid"><div className="enquiry-copy reveal"><p className="eyebrow"><span></span> Begin a conversation</p><h2>Let&apos;s find the<br /><i>right next step.</i></h2><p>Tell us a little about your family and the school team will get back to you with the information you need.</p><div className="enquiry-actions"><a className="button button-outline" href="/admissions">Explore Admissions <Icon name="arrow-up-right" size={15} /></a><a className="button button-orange" href="#enquiry-form">Enquire Now <Icon name="arrow-up-right" size={15} /></a></div><div className="contact-note"><span className="note-icon"><Icon name="pin" size={16} /></span><div><strong>Visit the school</strong><p>M-1 Jigisha, N-7, CIDCO<br />Chhatrapati Sambhajinagar<br />Maharashtra 431003, India</p></div></div></div><EnquiryForm /></div></section>

    <InitiativesSection /><AchievementsSection /><GallerySection /><NewsSection />

    <section className="section faq-section"><div className="shell faq-grid"><div className="faq-intro reveal"><p className="eyebrow"><span></span> Common questions</p><h2>Good to <i>know.</i></h2><p>Can&apos;t find what you&apos;re looking for? Our enquiry form is the quickest way to start a conversation.</p><a className="text-link" href="/contact">Ask us directly <Icon name="arrow-up-right" size={15} /></a></div><div className="faq-list">{faqs.map(([question, answer], index) => <FaqItem key={question} question={question} answer={answer} openByDefault={index === 0} />)}</div></div></section>
    <ContactSection />

    <section className="closing-banner"><div className="shell closing-inner"><p className="eyebrow eyebrow-light"><span></span> Your next chapter</p><h2>Come curious.<br /><i>Leave inspired.</i></h2><a className="button button-orange" href="#enquiry">Start an enquiry <Icon name="arrow-up-right" size={15} /></a></div></section>
  </main>
}

function Reveal({ children, className = '', delay = 0 }) {
  const elementRef = useRef(null)
  const isInView = useInView(elementRef, { once: true, margin: '-60px' })
  const reduceMotion = useReducedMotion()
  return <motion.div ref={elementRef} className={className} initial={reduceMotion ? false : { opacity: 0, y: 24 }} animate={isInView ? { opacity: 1, y: 0 } : undefined} transition={reduceMotion ? { duration: 0 } : { duration: 0.65, delay, ease: [0.22, 1, 0.36, 1] }}>{children}</motion.div>
}

function StatsSection() {
  return <section className="stats-section"><div className="shell stats-grid"><div className="stats-intro"><p className="eyebrow eyebrow-light"><span></span> A growing story</p><h2>Built for <i>what&apos;s next.</i></h2><p>These markers will become a living snapshot of the Jigisha community as verified school information is confirmed.</p></div><div className="stats-list">{schoolStats.map((stat, index) => <Reveal className="stat-item" delay={index * 0.08} key={stat.label}><strong>{stat.value === null ? '—' : <StatNumber value={stat.value} />}{stat.value !== null ? stat.suffix : ''}</strong><span>{stat.label}</span><small>{stat.value === null ? 'To be confirmed' : 'Jigisha snapshot'}</small></Reveal>)}</div></div></section>
}

function StatNumber({ value }) {
  const reduceMotion = useReducedMotion()
  return <motion.span initial={reduceMotion ? false : { opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ duration: .5 }}>{value}</motion.span>
}

function FacilitiesSection() {
  return <section className="section facilities-section"><div className="shell"><div className="section-head split-head"><div><p className="eyebrow"><span></span> Spaces for growth</p><h2>Room to <i>become.</i></h2></div><p>A considered visual index for learning, discovery, movement and making.</p></div><div className="facilities-grid">{facilities.map((facility, index) => <Reveal className={`facility-card ${facility.tone}`} delay={index * .07} key={facility.number}><div className="facility-art">{facility.image ? <img className="facility-image" src={facility.image} alt={facility.title} loading="lazy" /> : <div className="facility-icon"><Icon name={facility.icon || 'sparkle'} size={34} /></div>}<span>{facility.number}</span><div className="facility-orbit"></div><div className="facility-orbit small"></div><b>J</b></div><div className="facility-copy"><h3>{facility.title}</h3><p>{facility.description}</p><a href="/gallery">View space <Icon name="arrow-up-right" size={15} /></a></div></Reveal>)}</div></div></section>
}

function InitiativesSection() {
  return <section className="section initiatives-section section-dark"><div className="shell"><div className="section-head split-head"><div><p className="eyebrow eyebrow-light"><span></span> Initiatives & programmes</p><h2>Ideas in <i>motion.</i></h2></div><p>Verified Jigisha initiatives and programmes will be shared here as they are confirmed.</p></div><div className="initiative-grid">{initiatives.map((initiative, index) => <Reveal className={`initiative-card ${initiative.tone}`} delay={index * .08} key={initiative.title}><div className="initiative-graphic">{initiative.image ? <img className="initiative-image" src={initiative.image} alt="" loading="lazy" /> : null}<span>0{index + 1}</span><div></div></div><div><p className="card-kicker">{initiative.category}</p><h3>{initiative.title}</h3><p>{initiative.description}</p><a className="text-link light-link" href={initiative.link}>Explore <Icon name="arrow-up-right" size={15} /></a></div></Reveal>)}</div></div></section>
}

function AchievementsSection() {
  const hasAchievements = false
  return <section className="section achievements-section"><div className="shell achievements-grid"><div><p className="eyebrow"><span></span> Achievements</p><h2>Celebrate the <i>journey.</i></h2><p className="muted-copy">Celebrating the achievements and milestones of our school community.</p><a className="text-link" href="/achievements">Achievements will be shared here <Icon name="arrow-up-right" size={15} /></a></div><div className="achievement-carousel" aria-label="Jigisha achievements"><div className="achievement-carousel-head"><span>{hasAchievements ? 'Verified milestones' : 'Awaiting verified milestones'}</span><div><button type="button" disabled={!hasAchievements} aria-label="Previous achievement"><Icon name="chevron-left" size={17} /></button><button type="button" disabled={!hasAchievements} aria-label="Next achievement"><Icon name="chevron-right" size={17} /></button></div></div><div className="achievement-empty"><span className="achievement-star"><Icon name="sparkle" size={30} /></span><span className="eyebrow"><span></span> Jigisha community</span><h3>Celebrating the moments<br /><i>that make us proud.</i></h3><p>Achievements and milestones will be shared here when they are ready.</p><div className="achievement-progress"><span></span></div></div></div></div></section>
}

function GallerySection() {
  const [active, setActive] = useState(null)
  const galleryItems = [...imageAssets.galleryImages.map((src, index) => ({ src, category: 'Campus', title: index === 0 ? 'Jigisha school building' : `Jigisha image ${index + 1}`, tone: 'gallery-photo' })), ...galleryVisuals]
  useEffect(() => {
    if (active === null) return undefined
    const onKeyDown = event => {
      if (event.key === 'Escape') setActive(null)
      if (event.key === 'ArrowRight') setActive(index => (index + 1) % galleryItems.length)
      if (event.key === 'ArrowLeft') setActive(index => (index - 1 + galleryItems.length) % galleryItems.length)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [active, galleryItems.length])
  const current = active === null ? null : galleryItems[active]
  return <section className="section gallery-section section-paper"><div className="shell"><div className="section-head split-head"><div><p className="eyebrow"><span></span> Gallery</p><h2>See the <i>possibility.</i></h2></div><p>The Jigisha school building anchors this visual journal. Additional verified school photography can join it here over time.</p></div><div className="gallery-grid">{galleryItems.map((item, index) => <Reveal className={`gallery-tile ${item.tone} gallery-${index + 1}`} delay={index * .05} key={`${item.title}-${index}`}><button className="gallery-trigger" onClick={() => setActive(index)} aria-label={`Open ${item.category} gallery image`}>{item.src ? <img className="gallery-image" src={item.src} alt={item.title} loading="lazy" /> : <div className="gallery-pattern"><span>J</span></div>}<div className="gallery-caption"><small>{item.category}</small><strong>{item.title}</strong><Icon name="arrow-up-right" size={17} /></div></button></Reveal>)}</div><a className="button button-outline" href="/gallery">Open the gallery <Icon name="arrow-up-right" size={15} /></a></div>{current ? <AnimatePresence><motion.div className="lightbox" role="dialog" aria-modal="true" aria-label={`${current.category} gallery image`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><button className="lightbox-close" onClick={() => setActive(null)} aria-label="Close gallery"><Icon name="close" size={25} /></button><button className="lightbox-nav lightbox-prev" onClick={() => setActive(index => (index - 1 + galleryItems.length) % galleryItems.length)} aria-label="Previous image"><Icon name="chevron-left" size={32} /></button><div className={`lightbox-art ${current.tone}`}>{current.src ? <img className="lightbox-image" src={current.src} alt={current.title} /> : <div className="gallery-pattern"><span>J</span></div>}<div className="lightbox-copy"><small>{current.category} / {String(active + 1).padStart(2, '0')}</small><h3>{current.title}</h3><p>{current.src ? 'Official Jigisha International School photograph.' : 'Additional verified photography can be added here.'}</p></div></div><button className="lightbox-nav lightbox-next" onClick={() => setActive(index => (index + 1) % galleryItems.length)} aria-label="Next image"><Icon name="chevron-right" size={32} /></button></motion.div></AnimatePresence> : null}</section>
}

function NewsSection() {
  const [items, setItems] = useState(newsItems)
  useEffect(() => {
    getNews().then(payload => { if (payload.items?.length) setItems(payload.items) }).catch(() => undefined)
    return undefined
  }, [])
  return <section className="section news-section"><div className="shell"><div className="section-head split-head"><div><p className="eyebrow"><span></span> News & events</p><h2>From the <i>community.</i></h2></div><p>School news and event updates will appear here.</p></div>{items.length ? <div className="news-grid">{items.map((item, index) => <Reveal className="news-card" delay={index * .07} key={item.title}><div className={`news-art news-art-${(index % 3) + 1}`}>{item.image ? <img src={item.image} alt="" loading="lazy" /> : null}<span>{String(index + 1).padStart(2, '0')}</span><b>J</b></div><div className="news-copy"><div><small>{item.date}</small><small>{item.category}</small></div><h3>{item.title}</h3><p>{item.text || item.description}</p><a href="/news">Read more <Icon name="arrow-up-right" size={15} /></a></div></Reveal>)}</div> : <div className="news-empty"><span className="news-empty-mark"><Icon name="sparkle" size={27} /></span><div><p className="eyebrow"><span></span> News & events</p><h3>School news and event updates will appear here.</h3><p>Verified announcements and community stories will be shared here when ready.</p></div><a className="text-link" href="/contact">Contact the school <Icon name="arrow-up-right" size={15} /></a></div>}</div></section>
}

function ContactSection() {
  return <section className="contact-section section-dark"><div className="shell contact-grid"><div><p className="eyebrow eyebrow-light"><span></span> Visit Jigisha</p><h2>Find your way<br /><i>to us.</i></h2><p className="contact-lead">Jigisha International School<br />M-1 Jigisha, N-7, CIDCO<br />Chhatrapati Sambhajinagar<br />Maharashtra 431003, India</p><a className="button button-orange" href="/contact">Contact the school <Icon name="arrow-up-right" size={15} /></a></div><div className="map-card"><div className="map-grid-lines"></div><div className="map-pin"><span>J</span></div><div className="map-label">N-7 · CIDCO<br /><strong>Jigisha International School</strong></div><span className="map-caption">Map integration ready</span></div></div></section>
}

const emptyEnquiry = { parent: '', student: '', email: '', mobile: '', grade: '', message: '' }

function EnquiryForm({ endpoint = 'enquiry' } = {}) {
  const [status, setStatus] = useState('idle')
  const [form, setForm] = useState(emptyEnquiry)
  const update = event => setForm(current => ({ ...current, [event.target.name]: event.target.value }))
  const submit = async event => {
    event.preventDefault()
    const values = Object.fromEntries(Object.entries(form).map(([key, value]) => [key, value.trim()]))
    if (values.parent.length < 2 || values.student.length < 2 || !/^\S+@\S+\.\S+$/.test(values.email) || values.mobile.length < 7 || !values.grade) { setStatus('error'); return }
    setStatus('loading')
    try {
      if (endpoint === 'admission') await submitAdmissionEnquiry(values)
      else await submitEnquiry(values)
      setForm(emptyEnquiry)
      setStatus('success')
    } catch { setStatus('error') }
  }
  if (status === 'success') return <div className="form-success reveal"><span className="success-mark"><Icon name="check" size={25} /></span><p className="eyebrow"><span></span> Thank you</p><h3>Your enquiry has been received.</h3><p>The school team will contact you with the next steps.</p><button type="button" className="text-link" onClick={() => setStatus('idle')}>Send another enquiry <Icon name="arrow-up-right" size={15} /></button></div>
  return <form id="enquiry-form" className="enquiry-form reveal delay-one" onSubmit={submit} noValidate><div className="form-heading"><span>Enquiry form</span><small>All fields marked * are required</small></div>{status === 'error' ? <p className="form-error" role="alert">Please check the required fields and try again. If the problem continues, contact the school directly.</p> : null}<div className="form-row"><label>Parent / guardian name *<input required minLength="2" name="parent" value={form.parent} onChange={update} placeholder="Your full name" /></label><label>Student name *<input required minLength="2" name="student" value={form.student} onChange={update} placeholder="Student's full name" /></label></div><div className="form-row"><label>Email address *<input required type="email" name="email" value={form.email} onChange={update} placeholder="you@example.com" /></label><label>Mobile number *<input required minLength="7" name="mobile" value={form.mobile} onChange={update} placeholder="Your mobile number" /></label></div><div className="form-row"><label>Grade / standard<select required name="grade" value={form.grade} onChange={update}><option value="">Select a grade</option><option>Early years</option><option>Primary school</option><option>Middle school</option><option>Secondary school</option><option>Not sure yet</option></select></label><label>What can we help with?<input name="message" value={form.message} onChange={update} placeholder="Tell us a little more" /></label></div><div className="form-footer"><p>By submitting, you agree that Jigisha may use these details to respond to your enquiry.</p><button className="button button-blue" type="submit" disabled={status === 'loading'}>{status === 'loading' ? 'Sending…' : 'Send enquiry'} <Icon name="arrow-up-right" size={15} /></button></div></form>
}

function ContactForm() {
  const [status, setStatus] = useState('idle')
  const [form, setForm] = useState({ name: '', email: '', message: '' })
  const update = event => setForm(current => ({ ...current, [event.target.name]: event.target.value }))
  const submit = async event => {
    event.preventDefault()
    const values = Object.fromEntries(Object.entries(form).map(([key, value]) => [key, value.trim()]))
    if (values.name.length < 2 || !/^\S+@\S+\.\S+$/.test(values.email) || values.message.length < 5) { setStatus('error'); return }
    setStatus('loading')
    try { await submitContact(values); setForm({ name: '', email: '', message: '' }); setStatus('success') } catch { setStatus('error') }
  }
  if (status === 'success') return <div className="form-success"><span className="success-mark"><Icon name="check" size={25} /></span><p className="eyebrow"><span></span> Thank you</p><h3>Your message has been received.</h3><p>The school team will contact you with the next steps.</p><button type="button" className="text-link" onClick={() => setStatus('idle')}>Send another message <Icon name="arrow-up-right" size={15} /></button></div>
  return <form id="contact-form" className="enquiry-form" onSubmit={submit} noValidate><div className="form-heading"><span>Contact form</span><small>All fields marked * are required</small></div>{status === 'error' ? <p className="form-error" role="alert">Please check the required fields and try again. If the problem continues, contact the school directly.</p> : null}<div className="form-row"><label>Your name *<input required minLength="2" name="name" value={form.name} onChange={update} placeholder="Your full name" /></label><label>Email address *<input required type="email" name="email" value={form.email} onChange={update} placeholder="you@example.com" /></label></div><label>How can we help? *<input required minLength="5" name="message" value={form.message} onChange={update} placeholder="Tell us a little more" /></label><div className="form-footer"><p>By submitting, you agree that Jigisha may use these details to respond to your message.</p><button className="button button-blue" type="submit" disabled={status === 'loading'}>{status === 'loading' ? 'Sending…' : 'Send message'} <Icon name="arrow-up-right" size={15} /></button></div></form>
}

function FaqItem({ question, answer, openByDefault }) {
  const [open, setOpen] = useState(openByDefault)
  return <div className={`faq-item ${open ? 'open' : ''}`}><button onClick={() => setOpen(!open)} aria-expanded={open}><span>{question}</span><b>{open ? '−' : '+'}</b></button><AnimatePresence initial={false}>{open ? <motion.div className="faq-answer-motion" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: .25 }}><p>{answer}</p></motion.div> : null}</AnimatePresence></div>
}

function InnerPage({ path }) {
  const config = pageConfig(path)
  return <main className="inner-page"><section className="inner-hero section-dark"><div className="shell inner-hero-grid"><div><p className="eyebrow eyebrow-light"><span></span> Jigisha International School</p><h1>{config.title}<br /><i>{config.italic}</i></h1><p>{config.intro}</p></div><div className="inner-emblem"><img src={logo} alt="Jigisha International School official crest" loading="lazy" /><span>Establishing a place<br />to learn & belong</span></div></div></section><section className="section page-content"><div className="shell page-content-grid"><aside><p className="eyebrow"><span></span> Explore</p><nav>{['/about', '/academics', '/why-jigisha', '/admissions', '/student-life', '/gallery', '/achievements', '/news', '/contact'].map(href => <a className={path === href ? 'active' : ''} href={href} key={href}>{pageTitle(href)} <Icon name="arrow-up-right" size={14} /></a>)}</nav></aside><div className="page-main"><div className="page-visual"><div className="page-visual-rings"></div><img src={logo} alt="Official Jigisha International School crest" loading="lazy" /><span>{pageTitle(path)} / Jigisha</span></div>{config.blocks.map((block, index) => <div className="content-block reveal" id={block.id} key={index}>{block.type === 'heading' ? <h2>{block.text}</h2> : block.type === 'list' ? <div className="content-list">{block.items.map(item => <div key={item[0]}><span>{item[0]}</span><div><h3>{item[1]}</h3><p>{item[2]}</p></div></div>)}</div> : <p>{block.text}</p>}</div>)}{path === '/admissions' ? <div className="page-form-section"><EnquiryForm endpoint="admission" /></div> : null}{path === '/contact' ? <div className="page-form-section"><ContactForm /></div> : null}</div></div></section></main>
}

function Footer() {
  return <footer className="site-footer"><div className="shell footer-top"><div className="footer-brand"><a className="brand brand-footer" href="/"><span className="brand-mark"><img src={logo} alt="" /></span><span className="brand-copy"><strong>Jigisha</strong><em>International School</em></span></a><p>A place to learn with curiosity, grow with confidence and belong with purpose.</p></div><div className="footer-column"><h4>Explore</h4><a href="/about">About school</a><a href="/academics">Academics</a><a href="/why-jigisha">Why Jigisha</a><a href="/admissions">Admissions</a></div><div className="footer-column"><h4>Discover</h4><a href="/student-life">Student life</a><a href="/gallery">Gallery</a><a href="/achievements">Achievements</a><a href="/news">News & events</a></div><div className="footer-column footer-address"><h4>Find us</h4><p>M-1 Jigisha, N-7, CIDCO<br />Chhatrapati Sambhajinagar<br />Maharashtra 431003, India</p><a href="/contact">Contact the school <Icon name="arrow-up-right" size={15} /></a></div></div><div className="shell footer-bottom"><span>© {new Date().getFullYear()} Jigisha International School</span><span>Made for curious minds <b><Icon name="sparkle" size={14} /></b></span><span><a href="/">Privacy</a> · <a href="/">Terms</a></span></div></footer>
}

function pageTitle(path) { return ({ '/about': 'About', '/academics': 'Academics', '/why-jigisha': 'Why Jigisha', '/admissions': 'Admissions', '/student-life': 'Student life', '/gallery': 'Gallery', '/achievements': 'Achievements', '/news': 'News', '/contact': 'Contact' })[path] || 'Jigisha' }

function pageConfig(path) {
  const base = {
    '/about': { title: 'A school shaped', italic: 'around possibility.', intro: 'A thoughtful beginning for learners, families and a community growing together.', blocks: [{ id: 'about-school', type: 'heading', text: 'Learning is more than a timetable.' }, { id: 'vision-&-mission', text: 'Jigisha International School is being built as a welcoming space for questions, confidence and connection. The school’s identity is rooted in the belief that education should help young people understand the world — and their place in it.' }, { id: "principal's-message", type: 'list', items: pillars.map(([n, t, x]) => [n, t, x]) }] },
    '/academics': { title: 'Make learning', italic: 'matter.', intro: 'An approach that values strong foundations, active thinking and the joy of finding things out.', blocks: [{ id: 'curriculum', type: 'heading', text: 'The classroom is a starting point.' }, { id: 'teaching-approach', text: 'Our academic approach is designed to keep learners engaged with ideas, people and the world around them. Detailed curriculum and grade information will be shared by the school team as it is confirmed.' }, { id: 'activities', type: 'list', items: [['01', 'Foundations', 'Clear concepts, good questions and a steady sense of progress.'], ['02', 'Application', 'Learning that connects to real situations and meaningful problems.'], ['03', 'Expression', 'Multiple ways to explain, make, present and understand.']] }] },
    '/why-jigisha': { title: 'The Jigisha', italic: 'difference.', intro: 'A human-scale idea of school: high expectations, open minds and a strong sense of belonging.', blocks: [{ id: 'our-difference', type: 'heading', text: 'The best learning feels personal.' }, { id: 'school-values', text: 'We are creating an environment where learners are known, supported and encouraged to take meaningful responsibility. Our values are lived through the everyday details of school life.' }, { id: 'learning-spaces', type: 'list', items: journey.slice(0, 4).map(card => [card.number, card.title, card.text]) }] },
    '/admissions': { title: 'Your next step', italic: 'starts here.', intro: 'Tell us what you need to know and the school team will help you move forward with clarity.', blocks: [{ id: 'admission-process', type: 'heading', text: 'A clear beginning matters.' }, { id: 'required-documents', text: 'Admission availability, grade details and required documents are best confirmed directly with the school. Use the enquiry form to start a conversation with the team.' }, { id: 'enquiry', type: 'list', items: [['01', 'Send an enquiry', 'Share a few details about your family and preferred grade.'], ['02', 'Speak with the school', 'Receive current information and guidance for your situation.'], ['03', 'Visit and decide', 'Take the next step when you have the clarity you need.']] }] },
    '/student-life': { title: 'A full life', italic: 'at school.', intro: 'The moments between lessons matter too: friendships, movement, creativity and discovery.', blocks: [{ id: 'events', type: 'heading', text: 'There is more than one way to learn.' }, { id: 'sports', text: 'Student life at Jigisha is designed to make space for collaboration, expression and active wellbeing. As programmes are confirmed, this space will grow with the school community.' }, { id: 'arts-&-culture', type: 'list', items: journey.map(card => [card.number, card.title, card.text]) }] },
    '/gallery': { title: 'See Jigisha', italic: 'in focus.', intro: 'A visual journal of the spaces, people and moments that make a school feel like a community.', blocks: [{ type: 'heading', text: 'Our story, pictured with care.' }, { text: 'The Jigisha school building photograph currently anchors this visual journal. Additional verified views can be added as they are shared.' }, { type: 'list', items: [['01', 'Campus', 'The places where everyday learning happens.'], ['02', 'Community', 'The people and moments that bring school life to colour.'], ['03', 'Celebration', 'The milestones, events and achievements we share.']] }] },
    '/achievements': { title: 'Every step', italic: 'counts.', intro: 'We will celebrate the milestones and moments that are meaningful to the Jigisha community.', blocks: [{ type: 'heading', text: 'A place for milestones.' }, { text: 'Verified achievements, awards and school milestones will be published here when ready. We will always keep this record accurate and useful for families.' }, { type: 'list', items: [['01', 'Learner growth', 'Recognising progress, effort and thoughtful contribution.'], ['02', 'Community moments', 'Celebrating the shared experiences that bring us together.']] }] },
    '/news': { title: "What's happening", italic: 'at Jigisha.', intro: 'Notes, announcements and stories from a school community taking shape.', blocks: [{ type: 'heading', text: 'The latest will be shared here.' }, { text: "School news and event updates will be published here when verified information is ready to share. For current information, please contact the school directly." }, { type: 'list', items: [['01', 'School updates', 'Important information for families and the wider community.'], ['02', 'Community stories', 'Small moments and big ideas from life at Jigisha.']] }] },
    '/contact': { title: "Let's talk", italic: 'about school.', intro: "We're here to help with the questions that matter to your family.", blocks: [{ type: 'heading', text: 'Find us in N-7, CIDCO.' }, { text: 'Jigisha International School\nM-1 Jigisha, N-7, CIDCO\nChhatrapati Sambhajinagar, Maharashtra 431003, India' }, { type: 'list', items: [['01', 'Enquiries', 'Use the enquiry form to share your questions and preferred contact details.'], ['02', 'School visit', 'Contact the school team to ask about the right time to visit.']] }] },
  }
  return base[path] || base['/about']
}

export default App
