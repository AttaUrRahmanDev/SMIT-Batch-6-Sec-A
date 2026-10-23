const heading = document.getElementById("heading");
// console.log("heading");
heading.innerText = "Welcome TO DOM";
// console.log(heading.innerText);

// heading.textContent="Hello Students"
// console.log(heading.textContent);



const messages = document.getElementsByClassName("message");
console.log(messages);
console.log(messages.length);

messages[1].innerText = "Second Paragraph With Extra Content.";

console.log(messages[1]);
console.log(messages[1].innerText)




const paras=document.getElementsByTagName("p")

for(let i=0;i<paras.length;i++){
    paras[i].style.color="white";
    paras[i].style.fontSize="20px";
    paras[i].style.background="black";
    

}
console.log(paras.length);


//Takes first p-querySelector
// const paragraphs=document.querySelector(".info")
// const paragraphs=document.querySelectorAll(".info")
// console.log(paragraphs)