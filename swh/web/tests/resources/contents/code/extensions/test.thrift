namespace * thrift.test

/**
 * Docstring!
 */
enum Numberz
{
  ONE = 1,
  TWO,
  THREE,
  FIVE = 5,
  SIX,
  EIGHT = 8
}

const Numberz myNumberz = Numberz.ONE;
// the following is expected to fail:
// const Numberz urNumberz = ONE;

typedef i64 UserId

struct Msg
{
  1: string message,
  2: i32 type
}
struct NestedListsI32x2
{
  1: list<list<i32>> integerlist
}
struct NestedListsI32x3
{
  1: list<list<list<i32>>> integerlist
}
service ThriftTest
{
  void        testVoid(),
  string      testString(1: string thing),
  oneway void testInit()
}

