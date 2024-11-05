import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { AnalysisData } from '../types';

interface AnalysisProps {
  data: AnalysisData;
}

const Analysis: React.FC<AnalysisProps> = ({ data }) => {
  return (
    <Box sx={{ mb: 4 }}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          📝 Document Summary
        </Typography>
        <Typography>{data.summary}</Typography>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          🎯 Extracted Requirements
        </Typography>
        <pre style={{ whiteSpace: 'pre-wrap' }}>
          {JSON.stringify(data.requirements, null, 2)}
        </pre>
      </Paper>

      <Typography variant="h5" gutterBottom>
        🔍 Matching Products
      </Typography>
      {data.product_matches.map((match, index) => (
        <Accordion key={match.material_code}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>
              {match.description} (Score: {match.match_score.toFixed(2)})
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="subtitle1">Product Details:</Typography>
            <pre style={{ whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(match.details, null, 2)}
            </pre>
            {match.relaxation_details && (
              <>
                <Typography variant="subtitle1">Relaxation Details:</Typography>
                <pre style={{ whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(match.relaxation_details, null, 2)}
                </pre>
              </>
            )}
          </AccordionDetails>
        </Accordion>
      ))}

      {data.cross_sell_recommendations && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h5" gutterBottom>
            🤝 Recommended Combinations
          </Typography>
          {data.cross_sell_recommendations.map((rec) => (
            <Accordion key={rec.material_code}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>
                  {rec.description} (Compatibility: {rec.compatibility_score.toFixed(2)})
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="subtitle1">Compatibility Analysis:</Typography>
                {Object.entries(rec.compatibility_details).map(([key, value]) => (
                  <Box key={key} sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      {key.replace(/_/g, ' ').toUpperCase()}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={Number(value) * 100}
                      sx={{ mb: 1 }}
                    />
                  </Box>
                ))}

                <Typography variant="subtitle1">Pairing Suggestions:</Typography>
                <ul>
                  {rec.pairing_suggestions.map((suggestion, idx) => (
                    <li key={idx}>{suggestion}</li>
                  ))}
                </ul>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}

      {data.sales_pitch && (
        <Paper sx={{ p: 3, mt: 3 }}>
          <Typography variant="h5" gutterBottom>
            💼 Generated Sales Pitch
          </Typography>
          <Typography>{data.sales_pitch}</Typography>
        </Paper>
      )}
    </Box>
  );
};

export default Analysis;
