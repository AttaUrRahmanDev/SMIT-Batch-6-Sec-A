// //Date & Time

// //Get the Current Date and Time

// const now=new Date()
// // console.log(now);

// console.log(now.getFullYear());
// console.log(now.getMonth());
// console.log(now.getDate());
// console.log(now.getDay());
// console.log(now.getHours());
// console.log(now.getMinutes());
// console.log(now.getSeconds());

// console.log(`${now.getDay()}/${now.getMonth()}/${now.getFullYear()}`);
// // console.log(`${now.getDay()}-${now.getMonth()}-${now.getFullYear()}`);

// const date1=new Date("2026-10-09");
// console.log(date1); //Fri Oct 09 2026 05:00:00 GMT+0500 (Pakistan Standard Time)

// //date1.getDate()

// let date2="2026-10-09";
// let date3="10-09-2026";
// let date4="09-10-2026";

// //Format Date and Time
// const now = new Date();
// console.log(now.toDateString());
// console.log(now.toTimeString());
// console.log(now.toISOString());

// Display a Friendly Date
// const now = new Date();
// const options = {
//   weekday: "long",
//   year: "numeric",
//   month: "long",
//   day: "numeric",
// };
// console.log(now.toLocaleDateString("en-PK", options));

// Calculate the Difference Between Dates
const startDate = new Date("2000-10-01");
const endDate = new Date("2026-10-09");
const difference = endDate - startDate;
const days = difference / (1000 * 60 * 60 * 24);
console.log(days / 365);
