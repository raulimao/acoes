const fs = require('fs');
try {
    const report = JSON.parse(fs.readFileSync('./lighthouse-final.json', 'utf8'));

    const fcp = report.audits['first-contentful-paint'];
    const legacyJs = report.audits['legacy-javascript-insight'];

    console.log('--- FINAL REPORT START ---');
    console.log(`FCP Display Value: ${fcp.displayValue}`);
    console.log(`FCP Numeric Value: ${fcp.numericValue} ms`);
    console.log(`Legacy JS Score: ${legacyJs.score}`); // 1 = Passed, < 1 = Failed

    if (legacyJs.details && legacyJs.details.items && legacyJs.details.items.length > 0) {
        console.log('Legacy JS Warnings Found:');
        legacyJs.details.items.forEach(item => {
            const urlSnippet = item.url ? item.url.split('/').pop() : 'inline/unknown';
            console.log(`- ${urlSnippet}: ${JSON.stringify(item)}`);
        });
    } else {
        console.log('Legacy JS: No specific items found (Clean).');
    }
    console.log('--- FINAL REPORT END ---');
} catch (e) {
    console.error('Error:', e);
}
