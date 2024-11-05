import React, { useState } from 'react';
import { Container, CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { brown, orange } from '@mui/material/colors';
import Header from './components/Header';
import FileUpload from './components/FileUpload';
import Analysis from './components/Analysis';
import QuestionAnswer from './components/QuestionAnswer';
import { AnalysisData } from './types';

const theme = createTheme({
  palette: {
    primary: brown,
    secondary: orange,
  },
});

function App() {
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [pdfContext, setPdfContext] = useState<string>('');

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Header />
        <FileUpload 
          onAnalysisComplete={(data, context) => {
            setAnalysisData(data);
            setPdfContext(context);
          }} 
        />
        {analysisData && (
          <>
            <Analysis data={analysisData} />
            <QuestionAnswer pdfContext={pdfContext} />
          </>
        )}
      </Container>
    </ThemeProvider>
  );
}

export default App;
