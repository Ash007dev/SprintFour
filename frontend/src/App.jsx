import { useState } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import InputScreen from './screens/InputScreen';
import OutputScreen from './screens/OutputScreen';
import SummaryScreen from './screens/SummaryScreen';
import ApiDocsScreen from './screens/ApiDocsScreen';

function App() {
  const [screen, setScreen] = useState('input'); // 'input' | 'output' | 'summary' | 'docs'
  const [result, setResult] = useState(null);
  const [inputText, setInputText] = useState('');

  const handleProcessed = (data, originalText) => {
    setResult(data);
    setInputText(originalText);
    setScreen('output');
  };

  const handleViewSummary = () => setScreen('summary');
  const handleBackToOutput = () => setScreen('output');
  const handleReset = () => {
    setResult(null);
    setInputText('');
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
            onViewSummary={handleViewSummary}
            onReset={handleReset}
          />
        )}
        {screen === 'summary' && result && (
          <SummaryScreen
            result={result}
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
