import { defineConfig } from "eslint/config";


const lintCustomConfig = [{
    rules: {
        'indent': ['error', 4, {SwitchCase: 1}],
        'linebreak-style': ['error', 'unix'],
        'max-len': ['error', {'code': 120}],
        'quotes': ['error', 'single'],
        'semi': ['error', 'always'],
        'no-unused-vars': ['warn', {args: 'none'}],
        'no-empty': ['warn'],
        'no-trailing-spaces': ['error'],
    },
}];


export default defineConfig(...lintCustomConfig);
