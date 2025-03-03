# Flashcards AI

## Overview
Flashcards AI is a web application designed to help users create, manage, and learn from flashcards. The application allows users to create flashcard sets, add flashcards, import flashcards from CSV files, and even generate answers for flashcard questions using AI.

## Architecture
- **Frontend**: Static content hosted on an S3 bucket.
- **Backend**: AWS Lambda functions accessible via API Gateway.
- **Database**: DynamoDB for storing flashcard data.

## Features
- **Flashcard Sets**: Organize flashcards into sets based on topics.
- **CRUD Operations**: Create, update, and delete flashcards.
- **Add Flashcard**: Add new flashcards to a set.
- **AI-Powered Suggestions**: Generate answers for flashcard questions using AI.
- **CSV Import**: Import flashcards from CSV files.
- **Export to CSV**: Export flashcards to CSV files.
- **Print Ready Sets**: Generate print-ready versions of flashcard sets.
- **View Flashcards**: View and learn from flashcards.

## Setup Instructions
1. **Create Virtual Environment**:
    ```sh
    python3 -m venv flashcards/
    ```

2. **Install Dependencies**:
    ```sh
    pip3 install -r requirements.txt
    ```

3. **Activate Virtual Environment**:
    ```sh
    source flashcards/bin/activate
    ```

4. **Deactivate Virtual Environment**:
    ```sh
    deactivate
    ```

5. **Install Platform-Specific Dependencies**:
    ```sh
    pip3 install --platform manylinux2014_aarch64 --only-binary=:all: -t package -r requirements.txt
    ```

## Usage
### Export Flashcards to CSV
To export flashcards from a set to a CSV file, use the `export_flashcards_to_csv` function:
