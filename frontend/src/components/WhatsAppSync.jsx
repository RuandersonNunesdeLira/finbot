export default function WhatsAppSync() {
  const botNumber = '554199807311'
  const defaultMsg = encodeURIComponent('Olá, qual o preço do bitcoin hoje?')
  const waLink = `https://wa.me/${botNumber}?text=${defaultMsg}`

  return (
    <div className="whatsapp-tab">
      <div className="whatsapp-card">
        <div className="wa-icon">WA</div>
        <h2>Teste nosso Assistente no WhatsApp</h2>
        <p>
          Clique no botão abaixo para enviar uma mensagem ao nosso bot financeiro.
          Uma mensagem será pré-preenchida para facilitar o teste!
        </p>
        <a href={waLink} target="_blank" rel="noopener noreferrer" className="wa-link">
          Conversar com FinBot
        </a>
      </div>
    </div>
  )
}
