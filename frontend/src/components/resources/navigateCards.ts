export function navigateCards(event: KeyboardEvent) {
  if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) return
  const container = event.currentTarget as HTMLElement
  const cards = Array.from(container.querySelectorAll<HTMLElement>('[data-resource-card][aria-disabled="false"]'))
  const index = cards.indexOf(event.target as HTMLElement)
  if (index < 0) return
  event.preventDefault()
  const origin = cards[index]!.getBoundingClientRect()
  const horizontal = event.key === 'ArrowLeft' || event.key === 'ArrowRight'
  const sign = event.key === 'ArrowLeft' || event.key === 'ArrowUp' ? -1 : 1
  let nearest: HTMLElement | undefined
  let score = Infinity
  for (const card of cards) {
    if (card === cards[index]) continue
    const rect = card.getBoundingClientRect()
    const dx = (rect.left + rect.right - origin.left - origin.right) / 2
    const dy = (rect.top + rect.bottom - origin.top - origin.bottom) / 2
    const forward = (horizontal ? dx : dy) * sign
    const sideways = Math.abs(horizontal ? dy : dx)
    if (forward <= 1 || (horizontal && sideways > origin.height / 2)) continue
    const distance = forward + sideways * 4
    if (distance < score) { nearest = card; score = distance }
  }
  nearest?.focus()
}
