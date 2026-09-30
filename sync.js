require('dotenv').config();
const fs = require('fs-extra');
const crypto = require('crypto');
const path = require('path');
const axios = require('axios');
const { execFileSync } = require('child_process');

/**
 * CONFIGURAÇÕES
 */
const CONFIG = {
    TOKEN: process.env.GITHUB_TOKEN,
    OWNER: process.env.GITHUB_OWNER,
    REPO: process.env.GITHUB_REPO,
    TAG: process.env.GITHUB_RELEASE_TAG || 'v1.0.0-assets',
    LARGE_THRESHOLD: 99, // MB
    RAW_BASE_URL: `https://raw.githubusercontent.com/${process.env.GITHUB_OWNER}/${process.env.GITHUB_REPO}/main/`,
    IGNORE_PATTERS: [
        '.git', '.github', 'sync.js', 'generate-manifest.js', '.env', '.env.example',
        'node_modules', 'package.json', 'package-lock.json', 'manifest-standard.json',
        'manifest-low.json', '.gitignore', 'journeymap/cache', 'logs', 'backups', '.bak',
        'config/nexars-drakoria-id-cache', 'config/worldedit/sessions',
        'config/worldedit/.archive-unpack', 'config/jei/world/local',
        'config/.puzzle_cache', 'config/bclib/cache.json',
        'config/voicechat/username-cache.json', 'config/inventory-particles/cache',
        'config/arkans-axp-outbox', 'config/chunky/tasks',
        'config/arkans-id-loader-levels.json', 'config/arkan_optimizer-history.json',
        'config/arkans-worldgen-debug-report.txt', 'config/arkans-worldgen-debug.properties',
        'config/resourceful-config-web.json', '.backup-', '.old', 'data/servers_playtime.dat'
    ]
};

const PACK_DESCRIPTOR_FILE = '.arkan-pack.json';

const githubApi = axios.create({
    baseURL: 'https://api.github.com',
    headers: {
        Authorization: `token ${CONFIG.TOKEN}`,
        Accept: 'application/vnd.github.v3+json'
    }
});

/**
 * UTILITÁRIOS
 */
async function calculateHash(filePath) {
    return new Promise((resolve, reject) => {
        const hash = crypto.createHash('sha1');
        const stream = fs.createReadStream(filePath);
        stream.on('data', data => hash.update(data));
        stream.on('end', () => resolve(hash.digest('hex')));
        stream.on('error', err => reject(err));
    });
}

// GitHub Raw serves the bytes stored in Git, after Git's clean/EOL filters.
// Hashing the Windows working-tree bytes made CRLF text files fail integrity
// checks after download. Compute the distribution bytes exactly as Git does.
function getGitDistributionBytes(file) {
    const objectId = execFileSync('git', ['hash-object', '-w', `--path=${file.relativePath}`, file.fullPath], { encoding: 'utf8' }).trim();
    return execFileSync('git', ['cat-file', 'blob', objectId], { encoding: null, maxBuffer: Math.max(file.size * 2, 10 * 1024 * 1024) });
}

async function getFiles(dir) {
    let results = [];
    const list = await fs.readdir(dir);
    for (const file of list) {
        const fullPath = path.resolve(dir, file);
        const relativePath = path.relative(process.cwd(), fullPath).replace(/\\/g, '/');
        
        if (CONFIG.IGNORE_PATTERS.some(p => relativePath.includes(p))) continue;

        const stat = await fs.stat(fullPath);
        if (stat && stat.isDirectory()) {
            results = results.concat(await getFiles(fullPath));
        } else {
            results.push({ fullPath, relativePath, size: stat.size });
        }
    }
    return results;
}

/**
 * GITHUB API WRAPPERS
 */
async function getOrCreateRelease() {
    try {
        const { data: release } = await githubApi.get(`/repos/${CONFIG.OWNER}/${CONFIG.REPO}/releases/tags/${CONFIG.TAG}`);
        return release;
    } catch (err) {
        if (err.response?.status === 404) {
            console.log(`📦 Criando nova Release Assets: ${CONFIG.TAG}...`);
            const { data: release } = await githubApi.post(`/repos/${CONFIG.OWNER}/${CONFIG.REPO}/releases`, {
                tag_name: CONFIG.TAG,
                name: `Assets do Modpack (${CONFIG.TAG})`,
                body: 'Arquivos pesados gerenciados automaticamente pelo script de sync.',
                draft: false,
                prerelease: false
            });
            return release;
        }
        throw err;
    }
}

async function uploadAsset(releaseId, filePath, fileName) {
    const stats = fs.statSync(filePath);
    const url = `https://uploads.github.com/repos/${CONFIG.OWNER}/${CONFIG.REPO}/releases/${releaseId}/assets?name=${encodeURIComponent(fileName)}`;
    
    console.log(`📤 Fazendo upload de ${fileName} (${(stats.size / 1024 / 1024).toFixed(2)} MB)...`);
    
    const fileData = fs.readFileSync(filePath);
    let lastError;
    for (let attempt = 1; attempt <= 4; attempt += 1) {
        try {
            const { data: asset } = await githubApi.post(url, fileData, {
                headers: {
                    'Content-Type': 'application/octet-stream',
                    'Content-Length': stats.size
                },
                maxContentLength: Infinity,
                maxBodyLength: Infinity,
                timeout: 10 * 60 * 1000
            });
            return asset;
        } catch (error) {
            lastError = error;
            const status = error.response?.status;
            if (status && status < 500 && status !== 429) throw error;
            if (attempt === 4) break;
            const delay = 1500 * (2 ** (attempt - 1));
            console.log(`⏳ Upload interrompido (${status || 'rede'}); nova tentativa ${attempt + 1}/4...`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
    throw lastError;
}

async function deleteAsset(assetId) {
    await githubApi.delete(`/repos/${CONFIG.OWNER}/${CONFIG.REPO}/releases/assets/${assetId}`);
}

async function labelAsset(assetId, hash) {
    await githubApi.patch(`/repos/${CONFIG.OWNER}/${CONFIG.REPO}/releases/assets/${assetId}`, {
        label: `sha1:${hash}`
    });
}

/**
 * CORE EXECUTION
 */
async function run() {
    if (!CONFIG.TOKEN || CONFIG.TOKEN.includes('seu_token')) {
        console.error('❌ Erro: GITHUB_TOKEN não configurado no arquivo .env');
        process.exit(1);
    }

    const startTime = Date.now();
    console.log('🚀 Iniciando Arkan Sync v3.0 (Single-Source)');

    const release = await getOrCreateRelease();
    const remoteAssets = release.assets;
    const localFiles = await getFiles(process.cwd());
    const largeFilesFound = [];
    const pack = await fs.readJson(PACK_DESCRIPTOR_FILE);
    if (
        pack.schemaVersion !== 1 ||
        pack.packId !== 'arkan' ||
        pack.displayName !== 'Arkan' ||
        pack.edition !== 'standard' ||
        typeof pack.version !== 'string' ||
        !pack.version
    ) {
        throw new Error(`Descritor canônico inválido: ${PACK_DESCRIPTOR_FILE}`);
    }

    const manifest = {
        schemaVersion: 2,
        pack,
        version: Date.now().toString(),
        generatedAt: new Date().toISOString(),
        files: []
    };

    for (const file of localFiles) {
        const sizeMB = file.size / 1024 / 1024;
        const isLarge = sizeMB > CONFIG.LARGE_THRESHOLD;
        const distributionBytes = isLarge ? null : getGitDistributionBytes(file);
        const hash = isLarge
            ? await calculateHash(file.fullPath)
            : crypto.createHash('sha1').update(distributionBytes).digest('hex');
        const fileName = path.basename(file.relativePath);

        let url = `${CONFIG.RAW_BASE_URL}${encodeURI(file.relativePath)}`;

        if (isLarge) {
            largeFilesFound.push(file.relativePath);
            
            // Verifica se o asset já existe na release
            const existingAsset = remoteAssets.find(a => a.name === fileName);
            
            if (existingAsset) {
                // Tamanho igual não prova conteúdo igual. O rótulo SHA-1 torna
                // os assets grandes tão verificáveis quanto os arquivos Raw.
                if (existingAsset.size !== file.size || existingAsset.label !== `sha1:${hash}`) {
                    console.log(`🔄 Atualizando asset: ${fileName} (conteúdo não confirmado)`);
                    await deleteAsset(existingAsset.id);
                    const uploadedAsset = await uploadAsset(release.id, file.fullPath, fileName);
                    await labelAsset(uploadedAsset.id, hash);
                    // Re-fetch assets info para pegar a nova URL
                    const updatedRelease = await getOrCreateRelease();
                    const newAsset = updatedRelease.assets.find(a => a.name === fileName);
                    url = newAsset.browser_download_url;
                } else {
                    url = existingAsset.browser_download_url;
                    console.log(`✅ Asset já está no GitHub: ${fileName}`);
                }
            } else {
                console.log(`➕ Novo arquivo grande detectado: ${fileName}`);
                const uploadedAsset = await uploadAsset(release.id, file.fullPath, fileName);
                await labelAsset(uploadedAsset.id, hash);
                const updatedRelease = await getOrCreateRelease();
                const newAsset = updatedRelease.assets.find(a => a.name === fileName);
                url = newAsset.browser_download_url;
            }
        }

        manifest.files.push({
            name: fileName,
            path: file.relativePath,
            hash: hash,
            size: isLarge ? file.size : distributionBytes.length,
            url: url
        });
    }

    // Limpeza: Remover assets da Release que não existem mais localmente
    for (const asset of remoteAssets) {
        const stillExists = localFiles.some(f => path.basename(f.relativePath) === asset.name && (f.size / 1024 / 1024) > CONFIG.LARGE_THRESHOLD);
        if (!stillExists) {
            console.log(`🗑️ Removendo asset obsoleto da Release: ${asset.name}`);
            await deleteAsset(asset.id);
        }
    }

    // Atualizar manifestos
    await fs.writeJson('manifest-standard.json', manifest, { spaces: 2 });
    // A edição LOW permanece indisponível e continua espelhada somente para
    // compatibilidade com Launchers antigos. Ela ganhará descritor próprio
    // quando existir como pacote real.
    await fs.writeJson('manifest-low.json', manifest, { spaces: 2 });

    // Atualizar .gitignore automaticamente com os arquivos grandes
    let gitignore = await fs.readFile('.gitignore', 'utf8');
    const ignoreSectionMarker = '# ARQUIVOS GRANDES (>99MB)';
    const splitGitignore = gitignore.split(ignoreSectionMarker);
    
    let newGitignore = splitGitignore[0] + ignoreSectionMarker + '\n' + largeFilesFound.join('\n');
    await fs.writeFile('.gitignore', newGitignore);

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log(`\n✨ Sincronização concluída em ${duration}s!`);
    console.log(`📝 Manifesto atualizado com ${manifest.files.length} arquivos.`);
    console.log(`🛡️  ${largeFilesFound.length} arquivos grandes protegidos no .gitignore.`);
    console.log('\n👉 Agora você pode dar: git add . && git commit -m "update" && git push');
}

run().catch(err => {
    console.error('❌ Erro crítico:', err.response?.data || err.message || err);
    process.exit(1);
});
