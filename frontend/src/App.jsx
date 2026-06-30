import { useState } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import InputScreen from './screens/InputScreen';
import OutputScreen from './screens/OutputScreen';
import SummaryScreen from './screens/SummaryScreen';
import ApiDocsScreen from './screens/ApiDocsScreen';

function App() {
  const [screen, setScreen] = useState('input');
  const [result, setResult] = useState(null);
  const [verification, setVerification] = useState(null);

  const handleProcessed = (data) => {
    setResult(data);
    setVerification(null);
    setScreen('output');
  };

  const handleVerified = (verifyData) => {
    setVerification(verifyData);
  };

  const handleViewSummary = () => setScreen('summary');
  const handleBackToOutput = () => setScreen('output');
  const handleReset = () => {
    setResult(null);
    setVerification(null);
    setScreen('input');
  };
  const handleShowDocs = () => setScreen('docs');

  return (
    <div className="min-h-screen flex flex-col">
      <Header onLogoClick={handleReset} />

      <main className="flex-grow">
        {screen === 'input' && (
          <InputScreen onProcessed={handleProcessed} />
        )}
        {screen === 'output' && result && (
          <OutputScreen
            result={result}
            verification={verification}
            onVerified={handleVerified}
            onViewSummary={handleViewSummary}
          />
        )}
        {screen === 'summary' && result && (
          <SummaryScreen
            result={result}
            verification={verification}
            onReset={handleReset}
            onBackToOutput={handleBackToOutput}
          />
        )}
        {screen === 'docs' && (
          <ApiDocsScreen onBack={handleReset} />
        )}
      </main>

      <Footer onDocsClick={handleShowDocs} />
    </div>
  );
}

export default App;
