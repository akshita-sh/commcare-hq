({
    mainConfigFile: "corehq/apps/hqwebapp/static/hqwebapp/js/requirejs_config.js",
    baseUrl: 'staticfiles',
    fileExclusionRegExp: /(^\.)|(\.css$)/,
    dir: 'staticfiles',
    allowSourceOverwrites: true,
    keepBuildDir: true,
    modules: [
        // Third-party modules
        {
            name: "hqwebapp/js/common",
        },
        {
            name: "hqwebapp/js/jquery-ui",
            exclude: ["hqwebapp/js/common"],
        },

        // Modules common to HQ
        {
            name: "hqwebapp/js/built",
            exclude: ["hqwebapp/js/common"],
        },

        // App-specific modules
        {
            name: "fixtures/js/built",
            exclude: ["hqwebapp/js/common", "hqwebapp/js/built"],
        },
    ],
});
