//wenda_auto_default_disabled 这行代码将使本auto默认不启用
func.push({
    name: "代码解释",
    question: async () => {
        zsk(false)
        add_conversation("user", app.question)
        Q = await send(app.question, app.question, false, [], {"func_mode": "ci"})
        app.loading = true
        if(/^\[Image\]/.test(Q)) {
            add_conversation("AI", '![](data:image/png;base64,' + Q.substring(7) + ")", no_history = true)
        } else {
            add_conversation("AI", Q)
        }
        app.loading = false
        save_history()
    },
})