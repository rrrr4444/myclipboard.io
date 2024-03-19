let copyBtn = document.querySelector("#copy-btn");
let copyIcon = document.querySelector("#copy-icon");
let refreshBtn = document.querySelector("#refresh-btn");
let refreshIcon = document.querySelector("#refresh-icon");
let pasteBtn = document.querySelector("#paste-btn");
let pasteInput = document.querySelector("#paste-input");
let clipboardContents = document.querySelector("#clipboard-contents");


new ClipboardJS("#copy-btn");
if (!ClipboardJS.isSupported())
{
    copyBtn.hidden = true;
    pasteBtn.hidden = true;
}

function urlify(text) {
    // from https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
    var urlRegex = new RegExp(/(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})/gi);
    
    return text.replace(urlRegex, (url) => {
        return '<a href="' + url + '" rel="noopener">' + url + '</a>';
    })
}

function showCopiedMessage() {
        if (copyIcon.className === "bi bi-check") {
            copyIcon.className = "bi bi-clipboard";
        }
        else {
            copyIcon.className = "bi bi-check";
        setTimeout(showCopiedMessage, 1500);
        }
    }

copyBtn.addEventListener("click", () => {
    // Copy button uses external script ClipboardJS to copy
    // This is just to show feedback
    showCopiedMessage();
});

refreshBtn.addEventListener("click", () => {
    refreshIcon.className = "bi bi-check";
    document.location.reload();
});

clipboardContents.innerHTML = urlify(clipboardContents.innerHTML);
navigator.clipboard.readText().then((text) => {
    pasteInput.value = text;
});
