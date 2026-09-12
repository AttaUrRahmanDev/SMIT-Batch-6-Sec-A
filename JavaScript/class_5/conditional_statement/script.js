/*
conditional statements:
if 
else
else if -Reserved Keywords

Ternary Opperator:
condiiton ? "Fullfilled" : "Not Fullfilled"

Switch Statement:
switch(condiiton){
    case 1:
        log
    case 2:
        log
    default:
        message
}
*/

// // let age = 10;
// let age = prompt("Enter your age: ",18);
// let gender = prompt("Enter your gender: ","male");
/*
if(condition){
    console.log(message)
}
    */

// if(age>=18){
//     document.write("You are eligible "); 
// }else{
//     document.write("You are not eligible ");
// }

// Ternary Operator-Used Only For Simple Conditions/One Condition.
// Alternative of If Else
// let result=age>=18 ? "You are eligible" :" You are not eligible";
// document.write(result);

// if(age>=18 && gender=="male" || gender=="Male" || gender=="MALE"){
//     document.write("Please visit the male voting booth");
// }
// else if(age>=18 && gender=="female" || gender=="Female" || gender=="FEMALE"){
//     document.write("Please visit the female voting booth");
// }
// else if(age<18 && gender=="male" || gender=="Male" || gender=="MALE"){
//     document.write("You are not eligible to vote.");
// }
// else if(age<18 && gender=="female" || gender=="Female" || gender=="FEMALE"){
//     document.write("You are not eligible to vote. ");
// }
// else{
//     document.write("Enter Correct Data");
// }


// let role="admin";
// let role="user";
// let email="xyz@gmail.com";
// let password=123;

// if (email === "xyz@gmail.com" && password === 321)  {
//     if(role=="admin"){
//         document.write("You Can Post");
//     }else{
//         document.write("You Can't Post ");
//     }

// }else{
//     document.write("Invalid Credentials");
// }

// Task: Write a program to take marks from user and display grade according to marks.

let marks=prompt("Enter Your Marks: ",0);
let grade;
if (marks>=90){
    grade="A+";
}else if(marks>=80){
    grade="A";}
else if(marks>=70){
    grade="B+";}
else if(marks>=60){
    grade="B";}
else if(marks>=50){
    grade="C";}
else
{
    grade="Fail";}
document.write("Your Grade is: " + grade);
    

