module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      [
        'module-resolver',
        {
          root: ['./'],
          alias: {
            '@': './',
            '@components': './components',
            '@constants': './constants',
            '@services': './services',
            '@stores': './stores',
            '@hooks': './hooks',
            '@utils': './utils',
            '@types': './types',
            '@assets': './assets',
            '@screens': './screens',
          },
        },
      ],
      // 'react-native-reanimated/plugin', // Removed - causes duplicate __self prop error
    ],
  };
};