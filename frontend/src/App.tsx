import { Routes, Route } from 'react-router-dom'
import { CommandCenter } from '@/pages/CommandCenter'
import { ConversationalWorkflow } from '@/pages/ConversationalWorkflow'
import { ExecutionPage } from '@/pages/ExecutionPage'
import { ResultsPage } from '@/pages/ResultsPage'

function App() {
  return (
    <div className="min-h-screen bg-background">
      <Routes>
        <Route path="/" element={<CommandCenter />} />
        <Route path="/workflow" element={<ConversationalWorkflow />} />
        <Route path="/execution" element={<ExecutionPage />} />
        <Route path="/results" element={<ResultsPage />} />
      </Routes>
    </div>
  )
}

export default App
