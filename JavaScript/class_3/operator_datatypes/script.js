/*
Operators:(operator,operand)
operator:(+,-,*,/,%,**,=,==,!=,>,<,>=,<=)
operand:data on which operator is applied

Expression:Combination of operators and operands is called expression
2+4
2,4 ->operant
+ ->operator

= ->assignment operator
== ->equality(don't check data type)
=== ->strict equality(check data type)

comparison operators:

>:greater than
<:less than
>=:greater than or equal to
<=:less than or equal to
!= :not equal to(don't check data type)
!== :strict not equal to(check data type)

++ ->increment operator
-- ->decrement operator

value++ ->increemnt(postfix)
value-- ->decrement(postfix)
++value ->increment(prefix)
--value ->decrement(prefix)

value+=2 ->increment by 2 (value = value + 2)
value-=2 ->decrement by 2 (value = value - 2)

console.log(2++); //3(2+1)
console.log(2--); //1(2-1)
*/
// let a = 10;
// let b = 20;
// console.log(a + b); // 30
// console.log(a - b); // -10
// console.log(a * b); // 200
// console.log(a / b); // 0.5
// console.log(b % a); // 0

// BODMASS:(Brackets, Orders, Division, Multiplication, Addition, Subtraction)

let result = (2 * (4 * 3)) / 5;
console.log(result); // 4.8

let input = 3;
console.log(input++); // 3
console.log(input); // 4
console.log(++input); // 5
// console.log(INPUT)
console.log(--input); // 4

let value = 5;
// value = value + 2; //value=5+2;
// value+=2; // value = value + 2
// console.log(value); // 7

// value=value-2; // value = value 5- 2
value -= 3; // value = value - 3
console.log(value); // 2

// Dynamic Data Type: JavaScript is a dynamically typed language, which means that you don't have to declare the data type of a variable explicitly. The data type is determined at runtime based on the value assigned to the variable. This allows for flexibility in coding, but it can also lead to unexpected behavior if not managed carefully.
// Note: In JavaScript, you can assign different types of values to the same variable at different times. For example, you can assign a number to a variable and later assign a string to the same variable without any issues. This is in contrast to statically typed languages where the data type of a variable must be declared and cannot change.
// No float, double, long, short, byte, char, boolean data types in JavaScript. All numbers are represented as floating-point values (double precision) in JavaScript. There is no separate data type for integers or floating-point numbers. The same variable can hold different types of values at different times. For example, you can assign a number to a variable and later assign a string to the same variable without any issues. This is in contrast to statically typed languages where the data type of a variable must be declared and cannot change.

// int a=10;
// a="Hello";

// Data Types
// typeof value -> returns the data type of the value
let c = 234;
// let c =23.4
// let c=-23.4;
// let c =-234;
console.log(typeof c); // number

let name = "Test";
// let name = 'Test';
console.log(name); // string
// let intro= 'My name is "Test"';
// let intro = "My name is 'Test'";
// console.log(intro); // string
let firstName = "Test ";
let lastName = "Khan";
// String concatination (+) symbol is used to join two strings together
let fullname = "My name is " + firstName + lastName;
console.log(fullname); // string

// Template Literals: Template literals are a way to create strings in JavaScript that allow for easier string interpolation and multi-line strings. They are enclosed by backticks (`) instead of single or double quotes. You can embed expressions inside template literals using the ${expression} syntax.

/*
Syntax:
`My namme is ${firstName} ${lastName}`
*/
console.log(`My name is ${firstName} ${lastName}`); // string
