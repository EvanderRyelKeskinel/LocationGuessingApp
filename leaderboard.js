const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const cheerio = require('cheerio'); // requirements

// Read the HTML file asynchronously
fs.readFile('./templates/leaderboard.html', 'utf-8', (err, data) => {
  if (err) {
    console.error('Error reading file:', err);
    return;
  }
    const db = new sqlite3.Database('App.db', (err) => { //connect to database
        if (err) {
        console.error('Error opening database:', err.message);
        } else {
        console.log('Connected to the SQLite database.');
        }
    });
    // Load the HTML content into cheerio
    const $ = cheerio.load(data);
   
    db.get("SELECT Highest_solo FROM Users ORDER BY Highest_solo DESC", (err, rows) => { 
        //select scores filtered from highest first
        if (err) {
            console.error('Error fetching data:', err.message);  
        }
        else {
            for (let i = 0; i < 5; i++) {
                $(`#score${i}`).html(rows[i]);
                // fill in rows from highest to lowest score
            }
        }
    });
    db.close()
    
    // Write the modified HTML back to the file
    fs.writeFile('./templates/leaderboard.html', $.html(), (err) => {
        if (err) {
        console.error('Error writing file:', err);
        return;
        }
        console.log('HTML file has been updated!');
    });

});


