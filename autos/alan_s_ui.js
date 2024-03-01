// ==UserScript==
// @name         Alan UI
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  AlanLee制作的webui
// @author       You
// @match        http://127.0.0.1:17860/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=0.1
// @grant        none
// ==/UserScript==
//wenda_auto_default_disabled 这行代码将使本auto默认不启用
app.plugins.push({ icon: "newspaper-variant", url: "/alan_ui.html",hide_title:true })