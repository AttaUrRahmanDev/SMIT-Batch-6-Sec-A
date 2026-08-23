/* 
Data Types
->There are two datatypes in JavaScript: Primitive and Non-Primitive.
>Primitive:It's hold single value.
>Non-Primitive: It's hold multiple values/Group Of Values.

->number
->string
->boolean
->undefined
->null
->symbol
->bigint


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

// Logical Operators

&& ->logical AND
|| ->logical OR
! ->logical NOT



*/
// Comparison Operators

// Equality

// let a = 20;
// let b = "20";
// let b = 20;

// console.log(a == b); //true
// console.log(a === b); //false

//Greater Than | Less Than

// console.log(a>b);
// console.log(a<b);
// console.log(a>=b);
// console.log(a!=b);
// console.log(a!==b);

// Logical Operators

let email = "test@gmail.com";
let password = "asdf123";
let termcondition = true;

// Table (AND)
/*
true true == true
false false = false
true false = false 
false true = false
*/

// console.log(email === "test@gmail.com" && password === "asdf123" && termcondition === true); //true

// Table (OR)
/*
true true == true
false false = false
true false = true 
false true = true
*/

// console.log(email === "test2@gmail.com" || password === "asdf123" || termcondition === true); //true











// let a = 10;
// console.log(typeof a);

// let name="test";
// console.log(typeof name);

// let isLogin = true;
// console.log(typeof isLogin);

// let b;
// console.log(b); //undefined
// console.log(typeof undefined);

// let c = null;
// console.log(c); //null
// console.log(typeof null); //object

// let d = Symbol("hello");
// let e = Symbol("hello");
// console.log(typeof d);
// console.log(d==e); //false
