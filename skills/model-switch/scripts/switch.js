#!/usr/bin/env node
/**
 * Model Switch - Wechsle zwischen free, premium und auto Modellen
 * Node.js Version - keine Python Abhaengigkeit
 * 
 * Ersetzt ALLE openrouter/* Eintraege durch das Zielmodell
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const CONFIG_PATH = path.join(process.env.USERPROFILE || process.env.HOME, '.openclaw', 'openclaw.json');
const BACKUP_PATH = path.join(process.env.USERPROFILE || process.env.HOME, '.openclaw', 'openclaw.json.backup');

// Modell-Kennungen
const FREE_MODEL = 'openrouter/openrouter/free';
const PREMIUM_MODEL = 'openrouter/minimax/minimax-m2.5';
const AUTO_MODEL = 'openrouter/auto';

const MODEL_MAP = {
    'free': FREE_MODEL,
    'premium': PREMIUM_MODEL,
    'auto': AUTO_MODEL,
};

const LABEL_MAP = {
    [FREE_MODEL]: 'Free',
    [PREMIUM_MODEL]: 'Premium',
    [AUTO_MODEL]: 'Auto',
};

function replaceAllOpenrouterModels(obj, targetModel) {
    let count = 0;
    if (Array.isArray(obj)) {
        for (let i = 0; i < obj.length; i++) {
            if (typeof obj[i] === 'object' && obj[i] !== null) {
                count += replaceAllOpenrouterModels(obj[i], targetModel);
            }
        }
    } else if (typeof obj === 'object' && obj !== null) {
        for (const key of Object.keys(obj)) {
            if ((key === 'model' || key === 'primary') && 
                typeof obj[key] === 'string' && 
                obj[key].startsWith('openrouter/') && 
                obj[key] !== targetModel) {
                obj[key] = targetModel;
                count++;
            } else if (typeof obj[key] === 'object' && obj[key] !== null) {
                count += replaceAllOpenrouterModels(obj[key], targetModel);
            }
        }
    }
    return count;
}

function findCurrentModels(obj) {
    const found = {};
    
    function scan(node) {
        if (Array.isArray(node)) {
            for (const item of node) {
                if (typeof item === 'object' && item !== null) {
                    scan(item);
                }
            }
        } else if (typeof node === 'object' && node !== null) {
            for (const key of Object.keys(node)) {
                if ((key === 'model' || key === 'primary') && 
                    typeof node[key] === 'string' && 
                    node[key].startsWith('openrouter/')) {
                    const model = node[key];
                    found[model] = (found[model] || 0) + 1;
                } else if (typeof node[key] === 'object' && node[key] !== null) {
                    scan(node[key]);
                }
            }
        }
    }
    
    scan(obj);
    return found;
}

function restartGateway() {
    const openclawCmd = path.join(process.env.ProgramFiles || 'C:\\Program Files', 'nodejs', 'openclaw.cmd');
    
    // Try openclaw.cmd first
    if (fs.existsSync(openclawCmd)) {
        try {
            execSync(`"${openclawCmd}" gateway restart`, { timeout: 20000, stdio: 'pipe' });
            return 'OK';
        } catch (e) {
            return `FEHLER: ${e.message}`;
        }
    }
    
    // Try npx openclaw
    try {
        execSync('npx openclaw gateway restart', { timeout: 20000, stdio: 'pipe' });
        return 'OK';
    } catch (e) {
        return `FEHLER: ${e.message}`;
    }
}

function main() {
    const args = process.argv.slice(2);
    const command = args[0]?.toLowerCase();
    
    if (!command) {
        console.log('Usage: switch.js free|premium|auto|status');
        console.log('');
        console.log('Commands:');
        console.log('  free     - Wechsle zu openrouter/openrouter/free');
        console.log('  premium  - Wechsle zu openrouter/minimax/minimax-m2.5');
        console.log('  auto     - Wechsle zu openrouter/auto');
        console.log('  status   - Zeige aktuelles Modell');
        process.exit(1);
    }
    
    // Check config exists
    if (!fs.existsSync(CONFIG_PATH)) {
        console.log(`FEHLER: Config nicht gefunden: ${CONFIG_PATH}`);
        process.exit(1);
    }
    
    let config;
    try {
        const content = fs.readFileSync(CONFIG_PATH, 'utf8');
        config = JSON.parse(content);
    } catch (e) {
        console.log(`FEHLER: Config konnte nicht gelesen werden: ${e.message}`);
        process.exit(1);
    }
    
    // STATUS
    if (command === 'status') {
        const found = findCurrentModels(config);
        const keys = Object.keys(found);
        
        if (keys.length === 0) {
            console.log('=== MODEL STATUS ===');
            console.log('Keine openrouter/* Modelle gefunden.');
            process.exit(0);
        }
        
        // Find most common
        let mostCommon = keys[0];
        for (const m of keys) {
            if (found[m] > found[mostCommon]) {
                mostCommon = m;
            }
        }
        
        const label = LABEL_MAP[mostCommon] || mostCommon;
        
        console.log('=== MODEL STATUS ===');
        console.log(`Aktuelles Modell: ${label} (${mostCommon})`);
        for (const [model, count] of Object.entries(found)) {
            const l = LABEL_MAP[model] || model;
            console.log(`  ${l}: ${model} (${count}x)`);
        }
        process.exit(0);
    }
    
    // Validate command
    if (!MODEL_MAP[command]) {
        console.log(`Unbekannter Befehl: ${command}`);
        console.log('Verfuegbar: free | premium | auto | status');
        process.exit(1);
    }
    
    const targetModel = MODEL_MAP[command];
    const label = LABEL_MAP[targetModel];
    
    // Already on target model?
    const found = findCurrentModels(config);
    const keys = Object.keys(found);
    let mostCommon = keys.length > 0 ? keys[0] : null;
    
    if (mostCommon === targetModel && keys.length === 1) {
        console.log(`Bereits auf ${label} (${targetModel})`);
        process.exit(0);
    }
    
    // Backup
    try {
        fs.copyFileSync(CONFIG_PATH, BACKUP_PATH);
    } catch (e) {
        console.log(`Backup-Warnung: ${e.message}`);
    }
    
    // Replace all openrouter/* with target model
    const totalChanged = replaceAllOpenrouterModels(config, targetModel);
    
    if (totalChanged === 0) {
        console.log('Keine Eintraege zum Aendern gefunden.');
        process.exit(0);
    }
    
    // Write config
    try {
        fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf8');
    } catch (e) {
        console.log(`FEHLER: Config konnte nicht geschrieben werden: ${e.message}`);
        process.exit(1);
    }
    
    console.log('=== MODEL GEWECHSELT ===');
    console.log(`Neues Modell: ${label} (${targetModel})`);
    console.log(`Eintraege geaendert: ${totalChanged}`);
    
    // Gateway restart
    const gwStatus = restartGateway();
    console.log(`Gateway restart: ${gwStatus}`);
    
    const now = new Date();
    console.log(`Zeit: ${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}`);
}

main();