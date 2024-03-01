// ==UserScript==
// @name         金融监管知识库
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  利用金融监管知识库回答问题
// @author       lyyyyy
// @match        http://127.0.0.1:17860/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=0.1
// @run-at       document-idle
// @grant        none
// ==/UserScript==
get_title_form_md = (s) => {
    console.log(s)
    try {
        return s.match('\\[(.+)\\]')[1]
    } catch {
        return s
    }
}
get_url_form_md = (s) => {
    console.log(s)
    try {
        return s.match('\\((.+)\\)')[1]
    } catch {
        return s
    }
}
window.answer_with_zsk = async (Q) => {
    app.chat.push({ "role": "user", "content": Q })
    checkPrompt = "你善于根据要求判断问题意图，并准确回答问题。请从下面的要求中选出最合适的一个意图，要求如下：\n"
     +"1. 如果是\"某系统或应用有哪些适用的监管政策\"意图，则直接回答'0'，不要解释\n"
     +"2. 如果是其他意图，则直接回答'1'，不要解释\n\n"
     +"问题："+Q
    checkResponse = await send(checkPrompt, keyword = Q, show = false)
    if(checkResponse=='0') {
        answer = {
            role: "AI",
            content: "适用《网络安全等级保护基本要求》监管政策"
        }
        app.chat.push(answer)
    } else {
        app.top_p = 0.2
        kownladge = (await find(Q, 5)).filter(i => !i.score || i.score < 200).map(i => ({
            title: get_title_form_md(i.title),
            url: get_url_form_md(i.title),
            content: i.content
        }))
        if (kownladge.length > 0) {
            answer = {
                role: "AI",
                content: "",
                sources: kownladge
            }
            app.chat.push(answer)
            result = []
            for (let i in kownladge) {
                answer.content = '正在查找：' + kownladge[i].title
                if (i > 3) continue
                /*let prompt = app.zsk_summarize_prompt + '\n' +
                    kownladge[i].content + "\n问题：" + Q*/
                let prompt = "从文档\n"
                +"\"\"\"\n"
                + kownladge[i].content + "\n"
                +"\"\"\"\n"
                +"中找问题\n"
                + Q + "\n"
                +"\"\"\"\n"
                +"的答案，找到答案就仅使用文档语句回答问题，找不到答案就用自身知识回答并且告诉用户该信息不是来自文档。\n\n"
                +"不要复述问题，直接开始回答。"

                result.push(await send(prompt, keyword = Q, show = false))
            }
            app.chat.pop()
            app.chat.pop()
            let prompt = app.zsk_answer_prompt + '\n' +
                result.join('\n') + "\n问题：" + Q
            return await send(prompt, keyword = Q, show = true, sources = kownladge)
        } else {
            app.chat.pop()
            sources = [{
                title: '未匹配到知识库',
                content: '本次对话内容完全由模型提供'
            }]
            return await send(Q, keyword = Q, show = true, sources = sources)
        }
    }
    // lsdh(false)
    /*app.top_p = 0.2
    app.chat.push({ "role": "user", "content": Q })
    kownladge = (await find(Q, 5)).filter(i => !i.score || i.score < 120).map(i => ({
        title: get_title_form_md(i.title),
        url: get_url_form_md(i.title),
        content: i.content
    }))
    if (kownladge.length > 0) {
        answer = {
            role: "AI",
            content: "",
            sources: kownladge
        }
        app.chat.push(answer)
        result = []
        for (let i in kownladge) {
            answer.content = '正在查找：' + kownladge[i].title
            if (i > 3) continue
            let prompt = app.zsk_summarize_prompt + '\n' +
                kownladge[i].content + "\n问题：" + Q
            result.push(await send(prompt, keyword = Q, show = false))
        }
        app.chat.pop()
        app.chat.pop()
        let prompt = app.zsk_answer_prompt + '\n' +
            result.join('\n') + "\n问题：" + Q
        return await send(prompt, keyword = Q, show = true, sources = kownladge)
    } else {
        app.chat.pop()
        sources = [{
            title: '未匹配到知识库',
            content: '本次对话内容完全由模型提供'
        }]
        return await send(Q, keyword = Q, show = true, sources = sources)
    }*/
}
func.push({
    name: "金融监管知识库",
    description: "通过金融监管知识库回答问题",
    question: async (Q) => {
        answer_with_zsk(Q)
    }
})
window.answer_with_fast_zsk = async (Q) => {
    // lsdh(false)
    app.top_p = 0.2
    kownladge = (await find(Q, app.zsk_step)).filter(i => !i.score || i.score < 120).map(i => ({
        title: get_title_form_md(i.title),
        url: get_url_form_md(i.title),
        content: i.content
    }))
    if (kownladge.length > 0) {
        if (app.llm_type == "rwkv") {
            let prompt = 'raw!Instruction: 深刻理解下面提供的信息，根据信息完成问答。\n\nInput: ' +
                kownladge.map((e, i) => i + 1 + "." + e.content).join('\n') + "\n\nResponse: Question: " + Q + "\nAnswer: "
            return await send(prompt, keyword = Q, show = true, sources = kownladge,
                addition_args = { cfg_factor: app.cfg_factor, cfg_ctx: Q })
        } else {

            let prompt = app.zsk_answer_prompt + '\n' +
                kownladge.map((e, i) => i + 1 + "." + e.content).join('\n') + "\n问题：" + Q
            return await send(prompt, keyword = Q, show = true, sources = kownladge)
        }
    } else {
        app.chat.pop()
        sources = [{
            title: '未匹配到知识库',
            content: '本次对话内容完全由模型提供'
        }]
        return await send(Q, keyword = Q, show = true, sources = sources)
    }
}