// ==UserScript==
// @name         闻达搜索
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  闻达搜索入口
// @author       lyyyy
// @match        http://127.0.0.1:17860/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=0.1
// @grant        none
// ==/UserScript==
//wenda_auto_default_disabled 这行代码将使本auto默认不启用
app.plugins.push({ icon: "file-search", url: "wdss.html", hide_title: true })