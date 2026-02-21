import { google } from 'googleapis';

export interface Question {
  grade: string;
  topic: string;
  score: number;
  wordLimit: string;
  conditions: string[];
  criteria: string;
}

export async function getQuestions(): Promise<Question[]> {
  const apiKey = process.env.GOOGLE_SHEETS_API_KEY;
  const sheetId = process.env.GOOGLE_SHEET_ID;

  if (!apiKey || !sheetId) {
    console.error('Missing Google Sheets API Key or Sheet ID');
    // Return mock data for testing if keys are missing (optional, but requested to "test code to display...").
    // If I return empty, the test will just show empty.
    // I will throw error or return empty.
    return [];
  }

  const sheets = google.sheets({ version: 'v4', auth: apiKey });

  try {
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: sheetId,
      range: 'A2:H', // Fetches columns A to H from the first sheet
    });

    const rows = response.data.values;
    if (!rows || rows.length === 0) {
      console.log('No data found.');
      return [];
    }

    return rows.map((row) => {
      // Row structure:
      // 0: Grade
      // 1: Topic
      // 2: Score
      // 3: Word count
      // 4: Condition 1
      // 5: Condition 2
      // 6: Condition 3
      // 7: Criteria

      const conditions: string[] = [];
      if (row[4]) conditions.push(row[4]);
      if (row[5]) conditions.push(row[5]);
      if (row[6]) conditions.push(row[6]);

      return {
        grade: row[0] || '',
        topic: row[1] || '',
        score: parseInt(row[2] || '0', 10),
        wordLimit: row[3] || '',
        conditions,
        criteria: row[7] || '',
      };
    });
  } catch (error) {
    console.error('The API returned an error: ' + error);
    return [];
  }
}
