
const fs = require('fs');
const path = require('path');

const townsPath = path.join(__dirname, 'public/data/towns.geojson');
const auditsPath = path.join(__dirname, 'public/data/audits.geojson');

console.log('Reading files...');
const townsData = JSON.parse(fs.readFileSync(townsPath, 'utf8'));
const auditsData = JSON.parse(fs.readFileSync(auditsPath, 'utf8'));

console.log(`Towns Features: ${townsData.features.length}`);
console.log(`Audits Features: ${auditsData.features.length}`);

const townIds = new Set();
const townNames = new Map();

let duplicateIds = 0;
townsData.features.forEach(f => {
    const id = f.properties.TOWN_ID;
    const name = (f.properties.CITY || f.properties.TOWN || '').toUpperCase().trim();
    
    if (townIds.has(id)) {
        duplicateIds++;
    }
    townIds.add(id);
    if (name) {
        townNames.set(name, id);
    }
});

console.log(`Unique Town IDs: ${townIds.size}`);
console.log(`Duplicate Town IDs: ${duplicateIds}`);
console.log(`Mapped Town Names: ${townNames.size}`);

// Check types
let townIdTypes = new Set();
townsData.features.forEach(f => townIdTypes.add(typeof f.properties.TOWN_ID));
console.log('Town ID Types in Towns:', Array.from(townIdTypes));
let minId = Infinity, maxId = -Infinity;
townsData.features.forEach(f => {
    const id = f.properties.TOWN_ID;
    if (typeof id === 'number') {
        minId = Math.min(minId, id);
        maxId = Math.max(maxId, id);
    }
});
console.log(`Town ID Range: ${minId} to ${maxId}`);

let matchedById = 0;
let matchedByName = 0;
let unmatched = 0;


auditsData.features.forEach(f => {
    let id = f.properties.TOWN_ID;
    const typeOfOriginal = typeof id;
    if (id) id = Math.floor(id);
    
    // Log first 5 audits to see raw values
    if (matchedById + unmatched < 5) {
        console.log(`Audit Sample: Raw ID=${f.properties.TOWN_ID} (${typeOfOriginal}), Processed=${id}`);
    }

    if (id && townIds.has(id)) {
        matchedById++;
    } else {
        const name = (f.properties['CITY/TOWN'] || f.properties.CITY || '').toUpperCase().trim();
        if (name && townNames.has(name)) {
            matchedByName++;
        } else {
            console.log(`Unmatched Audit: ID=${id}, Name=${name}`);
            unmatched++;
        }
    }
});

console.log(`Matched by ID: ${matchedById}`);
console.log(`Matched by Name: ${matchedByName}`);
console.log(`Unmatched: ${unmatched}`);
