document.addEventListener('DOMContentLoaded', () => {

    const dbForm = document.getElementById('upload-database-form');
    const dbBtn = document.getElementById('upload-db-btn');
    const dbLoader = document.getElementById('db-loader');
    const statusDiv = document.getElementById('status');
    const resetDbBtn = document.getElementById('reset-db-btn'); // Get the new button

    const matchForm = document.getElementById('find-match-form');
    // ... (rest of the variable definitions are the same)
    const matchBtn = document.getElementById('find-match-btn');
    const matchLoader = document.getElementById('match-loader');
    const matchStatusDiv = document.getElementById('match-status');
    const resultsArea = document.getElementById('results-area');
    const queryImgDisplay = document.getElementById('query-img-display');
    const matchesContainer = document.getElementById('matches-container');
    const matchesTitle = document.getElementById('matches-title');

    // Handle Database Upload (Additive)
    dbForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        dbBtn.disabled = true;
        resetDbBtn.disabled = true; // Disable reset button during upload
        dbLoader.style.display = 'block';
        statusDiv.textContent = 'Adding images... This may take a moment.';
        resultsArea.style.display = 'none';

        const formData = new FormData(dbForm);

        try {
            const response = await fetch('/upload_database', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            if (response.ok) {
                statusDiv.textContent = result.message; // Display the new, more informative message
                statusDiv.style.color = 'green';
            } else {
                statusDiv.textContent = `Error: ${result.error}`;
                statusDiv.style.color = 'red';
            }
        } catch (error) {
            statusDiv.textContent = `Network Error: ${error.message}`;
            statusDiv.style.color = 'red';
        } finally {
            dbBtn.disabled = false;
            resetDbBtn.disabled = false;
            dbLoader.style.display = 'none';
            dbForm.reset(); // Clear the file input
        }
    });

    // NEW: Handle Reset Database
    resetDbBtn.addEventListener('click', async () => {
        if (!confirm('Are you sure you want to delete all images in the database? This action cannot be undone.')) {
            return;
        }

        dbBtn.disabled = true;
        resetDbBtn.disabled = true;
        dbLoader.style.display = 'block';
        statusDiv.textContent = 'Clearing database...';

        try {
            const response = await fetch('/reset_database', {
                method: 'POST'
            });
            const result = await response.json();
            if (response.ok) {
                statusDiv.textContent = result.message;
                statusDiv.style.color = 'blue';
            } else {
                statusDiv.textContent = `Error: ${result.error}`;
                statusDiv.style.color = 'red';
            }
        } catch (error) {
            statusDiv.textContent = `Network Error: ${error.message}`;
            statusDiv.style.color = 'red';
        } finally {
            dbBtn.disabled = false;
            resetDbBtn.disabled = false;
            dbLoader.style.display = 'none';
        }
    });


    // Handle Find Matches (this function remains exactly the same as before)
    matchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const queryImageInput = document.getElementById('query-image');
        if (queryImageInput.files.length === 0) { /* ... */ return; }
        matchBtn.disabled = true;
        matchLoader.style.display = 'block';
        matchStatusDiv.textContent = 'Searching for matches...';
        resultsArea.style.display = 'none';
        matchesContainer.innerHTML = '';
        try {
            const response = await fetch('/find_match', { method: 'POST', body: new FormData(matchForm) });
            const result = await response.json();
            if (response.ok) {
                queryImgDisplay.src = URL.createObjectURL(queryImageInput.files[0]);
                const matches = result.matches;
                if (matches.length > 0) {
                    matchesTitle.textContent = `Found ${matches.length} Similar Face(s)`;
                    matches.forEach(match => {
                        const matchItem = document.createElement('div');
                        matchItem.className = 'match-item';
                        const img = document.createElement('img');
                        img.src = `/database_images/${match.filename}`;
                        const scoreP = document.createElement('p');
                        const score = (match.similarity * 100).toFixed(2);
                        scoreP.innerHTML = `<b>Score:</b> ${score}%`;
                        matchItem.appendChild(img);
                        matchItem.appendChild(scoreP);
                        matchesContainer.appendChild(matchItem);
                    });
                } else {
                    matchesTitle.textContent = 'No Similar Faces Found';
                }
                resultsArea.style.display = 'block';
                matchStatusDiv.textContent = '';
            } else {
                matchStatusDiv.textContent = `Error: ${result.error}`;
                matchStatusDiv.style.color = 'red';
            }
        } catch (error) {
            matchStatusDiv.textContent = `Network Error: ${error.message}`;
            matchStatusDiv.style.color = 'red';
        } finally {
            matchBtn.disabled = false;
            matchLoader.style.display = 'none';
        }
    });
});