/**
 * SafeExit — always-visible quick escape button.
 * One tap takes the user to a neutral site and clears browser history.
 * Critical for victims who may be monitored.
 */
interface Props {
  lang: 'de' | 'en'
}

export default function SafeExit({ lang }: Props) {
  const handleExit = () => {
    // Replace current history entry so back button doesn't return here
    window.location.replace('https://www.google.com/search?q=wetter')
  }

  return (
    <button
      onClick={handleExit}
      className="fixed bottom-4 right-4 z-50 bg-slate-700 hover:bg-red-800 border border-slate-600 hover:border-red-600 text-slate-300 hover:text-white text-xs font-semibold px-3 py-2 rounded-lg shadow-lg transition-all duration-150 flex items-center gap-1.5"
      title={lang === 'de' ? 'Seite sofort verlassen' : 'Leave page immediately'}
      aria-label={lang === 'de' ? 'Seite sofort verlassen' : 'Leave page immediately'}
    >
      <span>✕</span>
      <span>{lang === 'de' ? 'Schnell verlassen' : 'Quick exit'}</span>
    </button>
  )
}
