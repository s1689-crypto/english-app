// Import necessary functions and types
import { getQuestions } from '../src/lib/sheets';
import * as dotenv from 'dotenv';
import path from 'path';

// Load environment variables from .env.local
dotenv.config({ path: path.resolve(__dirname, '../.env.local') });

async function main() {
  console.log('Fetching questions from Google Sheets...');
  try {
    const questions = await getQuestions();
    console.log('Successfully fetched questions:');
    console.log(JSON.stringify(questions, null, 2));
  } catch (error) {
    console.error('Error fetching questions:', error);
  }
}

main();
