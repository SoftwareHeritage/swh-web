print "I am #{math.random! * 100}% sure."

my_function = (name="something", height=100) ->
  print "Hello I am", name
  print "My height is", height

my_function dance: "Tango", partner: "none"

my_func 5,4,3,      -- multi-line arguments
  8,9,10

table = {
  name: "Bill",
  age: 200,
  ["favorite food"]: "rice",
  :keyvalue,
  [1+7]: 'eight'
}

class Inventory
  new: =>
    @items = {}

  add_item: (name) =>
    if @items[name]
      @items[name] += 1
    else
      @items[name] = 1

inv = Inventory!
inv\add_item "t-shirt"
inv\add_item "pants"

import
  assert_csrf
  require_login
  from require "helpers"