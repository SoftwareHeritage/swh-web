@CLASS
base

@USE
module.p

@BASE
class

# Comment for code
@create[aParam1;aParam2][local1;local2]
  ^connect[mysql://host/database?ClientCharset=windows-1251]
  ^for[i](1;10){
    <p class="paragraph">^eval($i+10)</p>
    ^connect[mysql://host/database]{
      $tab[^table::sql{select * from `table` where a='1'}]
      $var_Name[some${value}]
    }
  }

  ^rem{
    Multiline comment with code: $var
    ^while(true){
      ^for[i](1;10){
        ^sleep[]
      }
    }
  }
  ^taint[^#0A]

@GET_base[]
## Comment for code
  # Isn't comment
  $result[$.hash_item1[one] $.hash_item2[two]]