let student1="Ahmed";
let student2="Waqas";
let studnet3="Saqib";
let studnet4="Ali";
let student5="Ihtisham";

// let students="Ahmed","Waqas","Saqib","Ali","Ihtisham";

let students=["Ahmed","Waqas","Ali","Saqib","Umar"];
console.log(students.splice(1,3)); //remove element in array and return new array of removed elements
// console.log(students);
// console.log(students.length); //5
// console.log(students[1]); //Waqas
// console.log(students[3]); //Saqib
// console.log(students[students.length-1]); //Umar

// console.log(students);
// students.push("Hello"); //add new element at the end of array
// students.push("hello123");

// console.log(students);

// students.pop(); //remove last element in array
// console.log(students);

// // Add new element at the start of array
// students.unshift("Arshid");
// console.log(students);

// students.shift(); //remove first element in array
// console.log(students);

// students[2]="Ali"; //update element in array
// console.log(students);
// students[students.length-1]="Ali"; //update last element in array

console.log(students);

// array_name.slice(starting_index,ending_index); //copy elements from array
// starting_index:included
// ending_index:excluded
// let top_10_student=students.slice(0,1); //copy first 3 elements from array
// console.log(students.slice(0,2)); //copy first 2 elements from array
// console.log(students.slice(1,4)); //copy first 4 elements from array
 // // console.log(top_10_student);

// students[2]="Naseeb"; //update element in array
// students[10]="Hello"; //update element in array
// console.log(students);

// students.splice(starting_index,number_of_elements_to_remove,element_to_add); //add/remove elements in array
// students.splice(starting_index,delete_count,add_element | Replace_element); 

// students.splice(2,1); //remove element in array
students.splice(3,1); //remove element in array
console.log(students);
students.splice(2,0,"Hello"); //add element in array
console.log(students);