import { NavLink } from 'react-router-dom'
import './Nav.css'

const links = [
  { to: '/', label: 'Overview', end: true },
  { to: '/flights', label: 'Live Flights' },
  { to: '/delays', label: 'Delay Stats' },
  { to: '/cascade', label: 'Cascade Risk' },
  { to: '/airports', label: 'Airports' },
]

function Nav() {
  return (
    <nav className="main-nav">
      {links.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          end={link.end}
          className={({ isActive }) => 'nav-link' + (isActive ? ' nav-link-active' : '')}
        >
          {link.label}
        </NavLink>
      ))}
    </nav>
  )
}

export default Nav