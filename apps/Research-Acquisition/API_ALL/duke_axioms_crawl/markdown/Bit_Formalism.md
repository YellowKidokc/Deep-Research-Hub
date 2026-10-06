[ ![next](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/next.png)](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/Set_Theory_Thought.html) [Set Theory of Thought](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/Set_Theory_Thought.html)   
[ ![previous](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/prev.png)](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/Null_Set.html) [The Null Set](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/Null_Set.html)   
**[Contents](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/Contents.html)** | [rgb Home](http://www.phy.duke.edu/~rgb) | [Philosophy Home](http://www.phy.duke.edu/~rgb/Philosophy/philosophy.php) | [_Axioms_](http://www.phy.duke.edu/~rgb/Philosophy/axioms.php) |   

* * *
Other Books by rgb: | [_The Book of Lilith_](http://www.phy.duke.edu/~rgb/Lilith/Lilith.php) | 
* * *
  

#  A Bit of Formalism
It is perhaps worthwhile to formalize this, to define and extend traditional naive set theory algebraically just a bit to encompass the null set, the ``set of all things that cannot be put into sets'', where we insist that all subsets in any set theory _already_ de facto include the empty set, so that this ``set'' isn't one and is necessarily distinct from the empty set. 
First, like good algebracians let us give the null set the symbol suggested above: ![$\\mu$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img67.png). This will help us differentiate it from the empty set ![$\\O = \\{\\}$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img68.png). To simplify the algebra and show cleanly that the empty set is inside of it, we will introduce at the beginning an ``empty object'' which is in our existential set Universe. Rather than introduce an extra ``empty object placeholder'' in a list of objects (which would work just fine) we will treat the _brackets themselves_ , the set boundary, as the empty object. 
Then given a Universal set ![$S$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img11.png) of objects ![$\\{a,b,c...\\}$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img69.png) with their identity subsets  ![$I_a = \\{a\\}, I_b = \\{b\\}, I_c = \\{c\\}...$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img70.png) (recognizable as permutations of all the group's objects one at a time and the _implicit_ empty identity subset ![$I_{\\O} = \\{\\}$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img71.png) (the permutation of all the group objects zero objects at a time), they can be grouped into subsets ![$A,B,C...$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img72.png) in many ways via the union process e.g. :  ![$A = I_a \\bigcup I_b = \\{a,b\\}$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img73.png) where in particular  ![$S = I_a
\\bigcup I_b \\bigcup I_c...$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img74.png). Each of these subgroups represents a unique (unordered) permutation of the set objects. Note well that _all sets_ include the brackets and hence the empty set. 
In spite of the apparently discrete index on the set objects, do not be fooled - this index is discrete only in the sense of indicating uniqueness and should not be taken to mean that we can actually algebraically _specify_ all the identity subsets for any given space in the sense of creating a mapping between some set of symbols and the set objects. In this I am being no sloppier, really, than any set theorist is when discussing a set ![$S$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img11.png) that might have infinite cardinality (uncountably infinitely many members) such as any interval of the real number line. 
In English, these existential set theoretic statements say that all things that exist (set objects) can be placed in identity subsets, the union of all things that exist is all things that exist and that all non-empty subsets of all things that exist can be built out of unions of identity subsets (all of which seems pretty obviously true, given a Universal set of ``things that exist'' and a union and permutation process capable of handling continuum manifolds if that is what the Universal set happens to be). 
Given this, the following three statements (plus the notion that any given subgroup can be formed by - or better yet selected out of the permutations of - the unions of identity groups) fully specify the notion of the Law of Identity: 
  
  
| ![\\begin{displaymath}
\\forall a \\in S: I_a \\bigcup I_a = I_a
\\end{displaymath}](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img75.png)  |  (3.4)  |  
| --- | --- |  
  

  
  
| ![\\begin{displaymath}
\\forall a \\in S: I_a \\bigcap I_a = I_a
\\end{displaymath}](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img76.png)  |  (3.5)  |  
| --- | --- |  
  

  
  
| ![\\begin{displaymath}
{\\rm if } a\\in S \\ne b\\in S, {\\rm then }I_a \\bigcap I_b = I_{\\O}
\\end{displaymath}](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img77.png)  |  (3.6)  |  
| --- | --- |  
  

In this approach we _do not require any special treatment of the empty set_ in the algebra. It is just the ``zero'' of the algebra and lies within it just as ![$x + 0 = x$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img78.png) in arithmetic so all numbers ``contain zero'', and ![$a \\in S$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img79.png) can be ![$a = \\O$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img80.png) (the empty object) as easily as a nonempty member. 
Now, however, we _add_ the following `black hole'' relations: 
  
  
| ![\\begin{displaymath}
\\forall a \\in S: I_a \\bigcap \\mu = \\mu
\\end{displaymath}](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img81.png)  |  (3.7)  |  
| --- | --- |  
  

  
  
| ![\\begin{displaymath}
\\forall a \\in S: I_a \\bigcup \\mu = \\mu
\\end{displaymath}](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img82.png)  |  (3.8)  |  
| --- | --- |  
  

where ![$a$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img83.png) can be any object _including the empty object_. 
These are _very different from the properties of the empty set!_ Set operations involving ![$\\mu$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img67.png) (the undefined or null set) are without exception themselves _undefined or null_. One _cannot_ in any sensible way take the union of ``undefined'' (which is neither an object nor the absence of an object) with a list of objects and end up with a list of objects, not even an empty one. Nor can one take the intersection. ![$\\mu$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img67.png) isn't, really, a set and doesn't live ``in'' the Universe ![$S$](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/img11.png). 
* * *
[ ![next](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/next.png)](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/Set_Theory_Thought.html) [Set Theory of Thought](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/Set_Theory_Thought.html)   
[ ![previous](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/prev.png)](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/Null_Set.html) [The Null Set](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/Null_Set.html)   
**[Contents](https://webhome.phy.duke.edu/~rgb/Philosophy/axioms/axioms/Contents.html)** | [rgb Home](http://www.phy.duke.edu/~rgb) | [Philosophy Home](http://www.phy.duke.edu/~rgb/Philosophy/philosophy.php) | [_Axioms_](http://www.phy.duke.edu/~rgb/Philosophy/axioms.php) |   

* * *
Other Books by rgb: | [_The Book of Lilith_](http://www.phy.duke.edu/~rgb/Lilith/Lilith.php) | 
* * *
Copyright © _2010-01-21_  
Duke Physics Department   
Box 90305   
Durham, NC 27708-0305 
