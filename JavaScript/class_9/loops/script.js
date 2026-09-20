/*
for(initialization; condition; update){
   body  // code to be executed
}

*/

/*Concept of for loop
1. Initialization: It is used to initialize the loop control variable. It is executed only once, at the beginning of the loop.
2. Condition: It is a boolean expression that is evaluated before each iteration of the loop. If the condition is true, the loop body is executed; if it is false, the loop terminates.
3. Update: It is used to update the loop control variable after each iteration of the loop. It can be an increment or decrement operation.

//Now Concept-While And For Loop

Used to execute a block of code repeatedly until a specified condition is true.used for iterating over arrays, objects, or other iterable data structures.

while loop-Used to execute a block of code repeatedly as long as a specified condition is true. for example, you can use a while loop to iterate over an array until a certain condition is met.iterations known before hand becuse we know the range of numbers we want to iterate over. for example, if we want to print numbers from 1 to 10, we can use a for loop because we know the range of numbers beforehand. in while loop, we may not know the number of iterations beforehand, as it depends on a condition that may change during the execution of the loop. for example, if we want to keep asking the user for input until they provide a valid response, we can use a while loop because we don't know how many times the user will need to be prompted. eg code:-
let i = 1;
while (i <= 10) {
  console.log(i);
  i++;
} 
  // See the difference between for loop and while loop. for loop is used when we know the number of iterations beforehand, while while loop is used when we don't know the number of iterations beforehand. for loop is more concise and easier to read, while while loop can be more flexible and powerful. for loop is generally preferred when we know the number of iterations beforehand, while while loop is preferred when we don't know the number of iterations beforehand.in some or most cases in while loops,we know number of iterations beforehand, but we use while loop because we want to check the condition before executing the code block. for example, if we want to print numbers from 1 to 10, but only if they are even, we can use a while loop to check the condition before printing the number. eg code:-
let i = 1;
while (i <= 10) {
  if (i % 2 == 0) {
    console.log(i);
  }
}
*/

for (let i = 1; i <= 10; i++) {
  // if(i%2==0)
  if (i % 2 != 0) {
    console.log("Atta" + i);
  }
}

//Experiment
//how many  even number in range of 15 to 45
//how many odd number in range of 15 to 45
//find odd number in range of 15 to 45
//find even number in range of 15 to 45

let evenNums = [];
for (let i = 15; i < 45; i++) {
  if (i % 2 == 0) {
    evenNums.push(i);
    //console.log(i);
  }
}
console.log(evenNums);
console.log(evenNums.length);

//For of loop-Used to iterate over iterable objects like arrays, strings, maps, sets, etc.
const fruits = ["Banana", "Apple", "Mango"];
const input_fruit = prompt("Enter Fruit Name: ");
for (const fruit of fruits) {
  if (input_fruit.toLowerCase() === fruit.toLowerCase()) {
    console.log("Yes Available: " + fruit);
  }
  console.log(fruit);
}

//For in loop-Used to iterate over the properties of an object,keys of an object, or the indices of an array.

//for of for arrays
const cartProducts = [
  { id: 1, name: "iPhone 15", price: 250000 },
  { id: 2, name: "Samsung Galaxy A15", price: 45000 },
  { id: 3, name: "Redmi Note 13", price: 55000 },
  { id: 4, name: "AirPods", price: 25000 },
  { id: 5, name: "USB Cable", price: 500 },
];

let totalProductPrice = 0;
for (let product of cartProducts) {
  totalProductPrice = totalProductPrice + product.price;
  console.log(product);
}
console.log(totalProductPrice);

//for in for objects

const studentDetails = {
  name: "Test",
  roll_no: 234,
  age: 234,
  section: "B",
};

for (let key in studentDetails) {
  console.log(key + ":" + studentDetails[key]);
}
