# Math Predicting the Death of Nations

**Channel:** [[Fractal Philosophy]] (`FP`) · Chapter 1 of 1 · Length — (prose source, no timestamps) · [[00 - Channel Summary]]

---

In this video we're
going to try to make some mathematical models of
the rise and fall of countries. We'll base this off the
work of Peter Turchin who's written a
number of books on the subject both looking
at historical trends and applying them to try
predicting the trajectories of countries like
the United States. You can tell by these titles
he isn't the most optimistic about the near future.
One of the things that sets Turchin apart is that he
explicitly writes out the formulas and data he's
basing his predictions off of. So we're going to
try diving into those equations to better
understand both his theories as well as other complex
dynamics. We're going to be looking at the simplest
version of the models he suggests from his
book Historical Dynamics both because it lets
us model everything in its totality whereas
more complicated models will have a number of variables that are
not really quantifiable in the same way and because as you'll see the math and
visualizations are going to get complicated enough just with
these simple models. So starting with the
most basic concept A big part of
understanding the models we're going to be
talking about here lies in having an intuitive
understanding of the difference between linear
and exponential growth. Linear growth like we
have on the left here means we have a
constant change over time. In this case we have 100 balls
being added to this pile every second. But in exponential growth
like we have on the right here the rate of change increases over time. Here I have the balls
splitting every second or so which means that as the
number of balls increase there'll be more
balls that are splitting and therefore the number of new balls added
each second is going to increase over time. The practical result
of this is that while exponential growth
might start slower because it's building over time by the end it
explodes way faster than linear growth. Now when you're trying
to mathematically model real life systems there's
a number of different techniques you can use.
For example you might know that the equation
for linear growth looks something like this
and the equation for exponential growth
looks something like this. But in this video
what we're going to be interested in is less
the full value of some variable at a specific time and more
the dynamics of how things are changing. Given where we are now in history what's
likely to happen in the next x years. And for that kind of
reasoning it's more helpful to look at what are called
differential equations. Differential equations
output the rate of change. And so linear growth
will look like this It's just a constant number. It's always a hundred
new population every second. Whereas exponential
growth will look like this - the rate of change is dependent
on the current population. And I think this is a much more
intuitive way of understanding the dynamics of
what's going on here. In our example it's really
obvious that below a hundred population the exponential
growth is going to be slower. But above a hundred
population it's going to be faster. And I think that kind of intuition is a lot
harder to get from the normal equations. So in this video you're
going to see a lot of differential equations
but we're also going to be using what's called
agent-based modeling. And that's what you
saw with the balls there. The idea here is that instead
of just manipulating numbers You can actually make a simulation of the
thing you're trying to model in real life. It's kind of like making
a little mock-up video game of the thing
you're trying to analyze. Here I'm not directly tracking
the population numbers at all. I'm just having each green ball independently decide when it reproduces
and then measuring how often that happens. As computers have gotten
better and better this is becoming an increasingly common way of
modeling complicated systems. And hopefully I can show in this video
that sometimes you can understand a
situation better by seeing the agent-based model
as opposed to looking at differential equations
or normal equations. So we're going to
start by trying to model a country's population.
And that broadly works according to exponential
growth. But in real life you can't just
exponentially grow forever. You'll eventually hit some
limit on space or resources or whatever that'll
slow down growth and eventually stop it. So for
our agent-based model we're going to start with
the same green balls to represent population
that we used earlier. But now we're also going to
have this big field of orange cubes that represent
resources. The pops will have to consume resources both
to survive and to reproduce. Each pop will first grab
up to five resources, place one at its home location it started at, and then the rest in a surplus zone. We'll then create a new green pop for
every four resources in this surplus zone and then send everyone
back to do it all again. As I speed this up you'll
see that the population keeps growing larger
and larger and the amount of resources they're
collecting keeps getting bigger and bigger too. But eventually we'll
reach this point when the pops can grab all the resources that are available. Now the
population is still going to be growing but each individual pop is collecting less
resources than they could so the growth is going to start slowing
down. Eventually we'll reach a saturation
point where there's only enough resources for
each pop to get what they need to survive and
there's no leftover resources left to reproduce. In
biology this model of exponential growth but
with diminishing returns is called logistic
growth. And if you go and look up the equation for logistic growth
you get something that looks like this: Which at least to me
is not really intuitive and easy to understand
what it's doing. But on the other hand if you look up the
equations for the differential equations for logistic growth
you can find stuff like this which to me is
way more intuitive. Here N is the population
size r is the rate of change and k is
the carrying capacity which in our case is the maximum
amount of resources that can be grabbed. If you remember our
differential equation for exponential growth was
just r times N. That is the base rate
of change multiplied by the number of population
that currently exists. So the only addition that logistic
growth is making is this element which you can pretty obviously see when
N is 0 or close to 0 this is around 1 And when N is about the
same as k this ends up being 0. So the rate of change
for low population numbers is going to be about
the same as exponential growth but as N approaches
k the rate of change is going to drop down to 0. When
logistic growth is applied to human population it sometimes gets called
Malthusian growth after the author Thomas Malthus who wrote a
book about this in 1798. To directly quote his words: "Population when unchecked increases in a
geometrical ratio and subsistence for man in an arithmetical ratio." Now this was written
over 200 years ago so the language being used
is a little different. For example in my
dialect of English the adjective version of 'arithmetic' is 'arithmetic'
not 'arithmetical' but he's basically talking about
the same thing we were. By geometrical he's
talking about exponential growth and by arithmetical
he's talking about linear growth or at least
close enough concepts. So he gives the example
that the United States doubles its population
every 25 years which is interestingly enough a
stat he got from Benjamin Franklin but that's a
whole other tangent. He expects that as of
1800 when he's writing this the US could maybe
double the amount of food they're producing in the
next 25 years to match that. But quoting him again here: "In
the next 25 years it is impossible to suppose that the produce
could be quadrupled. It would be contrary
to all our knowledge of the quantities of the land." So he thinks the amount of food
produced in the US could maybe be doubled what it is in 1800
but certainly not quadrupled that. No amount of better farming or
land management could get over that. And uh I don't know if
you've been paying attention but let me just pull up this Wikipedia
page about agriculture in the US. Um from 1997 to 2014
we doubled the amount of food we produced. His ideas of
the theoretical limits are so far below what they actually were.
And that's because he didn't really fully comprehend the effects of
things like the industrial revolution. The US didn't quite
double its population every 25 years like he said
the utmost limit could be but our population
now is like 70 times bigger than when he
was alive. And in general there's like 8 times as many
people on the planet now. And I think that's
important to bring up here because a lot of times
modeling future situations like this you're going
to be wrong. But that doesn't mean the
underlying logic is incorrect. People today generally agree
with the ideas that Malthus put forward but turns out
that real life was a lot more complicated. There
were other things he wasn't taking into account when
he gave his upper limits of human growth both like
technologically but also socially. Like if you look at birth rates today
lots of countries are making more food than ever but have their
birth rates going down. The decisions of individual
people is a lot more complicated than
just food in babies out. Now despite Malthusian
growth being not accurate to how population works
anymore it's still the basis of the structural
demographic theory that Turchin is arguing
applies to today. But it's applied in a kind of
more metaphorical sense. The idea is that while
populations aren't quite following this there are
other processes that are analogous that are
still following a model of exponential growth
with diminishing returns. For example things like
supply versus demand curves where initially you're going
to get increasing returns on your investment but
eventually you're going to saturate a market and get
lower returns. We'll talk more about that later but
we're going to keep going with the basic pre-industrial
version as that's just simpler to model
for now. So as our next step to get a little more
realistic than the basic Malthusian model we're
going to add a concept of a state that takes in
some resources as taxation and then uses those to
increase the total amount of resources available. The
idea is this is analogous to something like
state-funded infrastructure or civil administration that
make it more efficient for people to get the
resources. So our agent-based model is going to start with
some of the same mechanics. We have pops that grab
resources from this big field place one at their
starting location that they used to eat and then place the rest
of what they gathered in a surplus zone. But now we have a
couple new mechanics. Some percentage of the
surplus resources collected is going to go to the
state as taxation Here represented by this
smaller box with the dotted line which is 20
percent of the surplus. The state also has expenses
which is this box here. In my example here
we're having the state need 0.2 resources for every
member of the population. If the state made more
money in taxation than it needs to expense then it can
store the rest in this box here. And finally we have the state increase
the supply of resources. So the bigger this box of state
resources is the bigger this box over here is and
this is bonus resources that are created by the state.
I realize that's a number of things to introduce at
once but the main thing is that this box is the
state's income and this box is the state's
expenses. So as long as the income box is bigger
than the expense box the state is making money
and the total supply of resources is going up.
But if the expense box is bigger then the state is
losing money every cycle and therefore the supply of
resources is going to go down. Now at this point I'm
going to speed up the simulation to see what
happens but I want you to try predicting what
you think the trajectory of the population size and the
state size is going to be as this runs. Keeping in mind that the state
expenses are based on the population size and the state income is based on
the amount of surplus resources. Okay let's look at some graphs
to talk about what happened there. So population over time of our first
Malthusian simulation looks like this. It starts out slow speeds up
and then slows down again. It starts out slow speeds up
and then slows down again. It starts out slow speeds up
and then slows down again. It starts out slow speeds up
and then slows down again. As it reaches the saturation point of 2500. If we compare that to
our new model with state taxes we'll see that
growth starts slower. And that's because a percent of
the surplus is going to the state and so less is going to
just growing the population. But because the state is then growing
the maximum amount of resources the population goes above
what it was in our old model. Population growth starts slowing
down as we reach this higher point. But instead of just
leveling out there it crashes way back down to that
base level we had before  Interestingly if we look at the state
resources compared to the population we see that they kind of
change at different rates with the state resources
starting to slow down and eventually dip before
the population crashes. The reason for this lag
is that state resources are dependent on the
surplus the population gathers and therefore indirectly on
the rate of change of the population. The state resources then feed back
into the rate of change of the population which causes it to snowball
even faster in its decline. Now like with Malthus I think this is still too simplistic to draw
conclusions about real life from but the concepts here
show up in a lot of areas. There's this phrase that
"Things change slowly and then all at once" This was originally used by Hemingway
to talk about a character going bankrupt but was also used by John Green to
talk about a character falling in love and was used by Atrioc to talk about
the AI bubble amongst other things. That's an interesting
collection of people to reference. But anyways you can see all
of these have this kind of idea of some kind of exponential
combined with linear things. Bankruptcy obviously makes a lot
of sense to what we're talking about. You can look at falling in love
as having exponential relations like I find someone more
attractive if they find me attractive. That's some exponential growth right there. And then there's some linear things
like the amount of time we spend together. For economic bubbles
if you look at a graph of the stock of Cisco
during the dot-com bubble it looks pretty suspiciously similar to
the graph we had here of population. You can even use roughly the same logic
where investment acts like population where it's going to
exponentially grow initially the more money you have the
faster you can grow kind of thing. And then there's an asymptotic limit
to how much that can grow in isolation. But then we can add something like
'hype' which is similar to state finances. It makes sense that
the hype around a stock would go up if the
stock is increasing fast which is the same as our
population having a large surplus. And it also makes sense
that the hype would go down if the total value
of the stock is high. People are more worried
that it's overvalued which is again like the exact same mechanism
as we were modelling with Population. You obviously can't actually model the
entirety of a market with two variables but just to emphasize that this
type of thinking is very important in a lot of situations other than
the one we're talking about here. *Sponsored Throat Clear* One way to improve your intuition for
exponential growth models like these is through the sponsor
of this video Brilliant who recently added a course
on exponential functions. Brilliant's interactive lessons mean
you're not just passively learning you're becoming an
active problem solver who can apply what you
know to new situations. And they're wide-court course
catalogue means you can find new things to learn that fit your interests
and current knowledge. I've personally been going through
their course on how AI works and have found the interactive
lessons and impressive visuals a refreshing change of pace for a
normally dense and literary subject. Brilliant let me customize the course
by skipping past things I already knew and push me to actually use that
knowledge with motivating challenges. If this sounds like something
you'd be interested in you can check it out for free at
brilliant.org/fractalphilosophy by scanning the QR code or
clicking the link in the description. Brilliant is also offering
viewers of this channel 20% off an annual
premium subscription Which will give you unlimited
daily access to everything on the site. Again thanks to Brilliant
for sponsoring this video. Alright so now I want
to try getting a little more insight into our
state financial model by looking at the differential
equations that model it. I'm going to show the actual
equations I'm using here but if you're just watching this video
casually don't really worry about it. We're going to get to some
interesting properties afterwards. I'm just including this
for the type of person who wants to pause and
try implementing it themselves. We can start with our population
growth equation from before and now instead of the carrying
capacity being a fixed value we're going to change that into
something that's dependent on the state. Here's an equation that gives diminishing
returns as the state resources increase and then we want to
add a second differential equation for how the
state finances work. This whole chunk of the
population growth equation is the amount of surplus
that a population gets so we can just plop that
into the state resources and multiply it by taxation rate
to get the state revenue. And then we take the
amount of population and multiply it by some value
to get state expenses. Again we use 20% for both of
these values in our agent-based model. Once we have our two
differential equations we can graph them in what's
called a phase space where we put our population on a y-axis
and our state finances on the x-axis. Now we can place a dot
somewhere on this graph and evaluate our differential
equation at that point to get a vector that
dot should move along. Here we can see our dot is at the
equilibrium point for our population and so if we raise the population
any higher it'll just fall back down. Our state finances are at zero because when
we're at the equilibrium point or higher all the food is being consumed
just to maintain the population. If we raise the state
funds any higher then we start the cycle of
state funds going up population going up and
then eventually crashing. You can see we get
different arcs of different sizes depending on how
much state finances we have. We can also lower the
population below that point and if we lower it far enough... that'll also start the cycle. Because once the population is low enough then each member of the population
will have a larger chunk of resources and there'll be enough
that state taxes can come in get some funds for the state
and start the cycle that way. I find it interesting that in this model
the state finance is nearly always zero which in real life would be a little more
complicated because like a lot of states can print money so conceptually a
state could have no money but still pay for things at the
cost of creating inflation. But again this is
intentionally a much simpler model than anything
going on in real life. Another neat thing we can do in this
phase space is put dots at multiple points and then run them all together
to help understand the overall movement pattern of the entire
system instead of just one run. And an interesting
thing to note here is that in phase space these
lines can never cross. That's because in phase
space a point is a set of values that then give the
vector of how they change. So for a line to cross that would
mean at the same point it would have to give two different values
for how it's gonna change. And this is significant because it
means for this kind of arcing behavior where the population goes
up but then goes down later that's only possible to do if
you have multiple variables. If you're just modeling the population
number you can't get this kind of behavior. Our population model
here always ends up at the same equilibrium point
no matter what you do. But there are some systems of differential
equations that can have stable loops. A famous example is
this predator prey model Here there's a number
of different stable loops depending on where
your initial condition was but you'll see again none
of them ever intersect. And actually quick programming
tangent while we're here - So the simplest way
to implement differential equations on a computer
is called Euler's method where you take the rate of change
you get from your differential equation and then just multiply that by the amount
of time it takes your computer to run that. So if you're running at like 60 frames
per second that's like 60 milliseconds. But the problem with that is that
sometimes you can overshoot curves. So like for these predator and prey equations if I increase
how fast we're running the simulation then my estimate overshoots the
curve and it gradually spirals out. If you notice earlier in the video
there were some distortion patterns with where resources were
being placed that's kind of similar. It's based on the computer's
approximation of some stuff. In pure math world this isn't a problem
because in theory you'd be running this infinite times per second but unfortunately
computers aren't quite that fast yet so we're gonna have
to use one of a bunch of algorithms to have a
better approximation. I'm using one called
RK4 where you take four different estimates
and then do a weighted average of them to try to get more stable. It's a whole thing but
anyways if you're trying to do this on your own know that
that's a component of this. From here we can look
at the final component of Turchin's structural
demographic theory which is to split the population
into two distinct populations one for the commoners
and one for the elites. In the pre-industrial
society the idea here is that instead of the state
directly taxing people there's like peasants
who are doing the actual farming and mining and production
of resources and then there's like nobility or some upper class that
is directly getting resources from them and then the state is just
taxing those rich nobility type. This is again an aspect you have to
abstract a bit to apply to modern societies so you can do something
like look at the ratio between the elites and
commoners as an analog for like wealth distribution or something
like that but for now we're just going to play it straight and have
these be like actual populations. Implementing that in our agent-based
model we now have these purple balls which act as the elites. These are
similar to the normal populations but they grab their resources
from the normal population surplus deposit one at their
starting location and then put their surplus in an
elite surplus location. This is way up here because we
need room for when things expand. The state works the same
as before but now the expenses are based on
the elite population numbers and its revenue is
based on the elite surplus. With all that in mind we'll run
it again and see what happens. So overall this model has very similar
dynamics to both of our previous ones. If you just look at the
population of the elites it's very similar to our
last model where they grow and then hit some point
and then collapse after that. And if you look at the
behavior of the general population it's very
similar to our first model. This all happens faster now
because we have the elite siphoning off some amount of resources
to feed themselves but it's overall generally
the same dynamic. This fact that sometimes you can add
a bunch of new mechanics and still get the same general
behavior is part of why it's good to keep your models
as simple as possible. Another thing worth
noting here is that when you get more complicated
models like this the amount of parameters we have that control
how things work keeps going up and up. So like in this model we
added a parameter for how many resources it takes for a
new elite pop to be created. And looking at this run
and seeing that the elites gradually took over the
entire supply of resources I want to try making
the elite growth rate go down so I increase this
value to 15 instead of 4. We're going to try to fast forward
through this run a little bit to save time but the interesting thing here is with just
that small modification it went from oh always plateauing and collapsing to
infinitely growing all three variables. When the elites grow slow
enough then that means that when they get bigger
the state gets bigger so then the supply gets bigger and
then the population rises to that supply. Turns out that the
only reason that wasn't happening before is
that the elite population was growing faster than
the normal population so the elites gradually took
all the available supplies. I honestly don't know how YouTube's bit
rate is going to make this look but from my perspective this is
some cool like abstract algorithm art type stuff
which is fun to look at but obviously not very realistic in the
infinite growth of resources in all aspects.  It's also a crazy testament to modern
computers that I'm getting like 15 FPS despite the tens of thousands of
things moving and happening every second. I'm going to post the source code
to this, this is like me trying to learn Unity ECS if you know what
that is but I don't know it's crazy. Anyways we're going to now
switch over to the differential equations because it's
a little easier to make changes quickly in
that. I don't have to code a bunch of new logic
and state machine type things for that to
happen. Here's the literal equations that Turchin
uses which are a little different in a couple
ways from our simulation. It's like the max carrying
capacity does have an upper limit and there's
like diminishing return on state resources. He
also has what I think a little less intuitive way
of how the elites get resources where he just
has at a certain number of elites they get a
fixed percentage of the resources and then at a certain number
of elites they get half of the resources. So like say at 100 elites
they're always going to get 50% of the resources
of the population even if the commoners have
a million or 10 million population 100 elites
will still get half of it. Which again is probably
abstracting some level of bureaucracy or whatever
but just to know that's a little different from what I
did in the agent based model. Despite those differences when we
go to our phase space which is *3D* now we can see that we get basically
the same behavior as before where population goes
up which leads to the elite population to go
up which leads to the state to go up but eventually this starts
getting reversed when state funds arc down which leads to a reverse
of all the other trends until everything collapses to 
a situation where there's no state Turchin does this by changing the equations a little
bit so instead of worrying about like carrying
capacity and things like that he simplifies it down and
just adds this component of elite extinction where
if there's no state the elite will die off really
quick and if there's a state that reduces the
rate of elite extinction. This could in theory be
modeling a lot of things You could consider something like a
legal system where what the state's main job
is is resolving conflicts between wealthy people
so they don't fight as much. In a more nihilistic
sense you could say that the state defends
the interests of the elite and without the state
the elite will get overrun by the commoners
or something like that. It could potentially mean a
lot of things but from a pure math perspective what
this does is drop elite numbers quicker once
the state goes broke which then gives room for the commoner
population to generate a tax base to get the elites
to have a tax base so then the state can restart
and loop the whole thing once again And you can see that
with those modified equations we do in fact see a cyclical
loop in our 3D space. One of the cool things
about this set of equations is that it creates a
limit cycle so we saw that even in 2D you can
have these stable loops and the predator prey
example had infinite number of these different stable
loops but our stable loop in 3D doesn't
quite work like that. If I pull any of the variables
off the loop it just gradually settles back down to that
same loop. It's topologically analogous to a shape like
this where you have a stable loop and then everything
inside that loop is going to gradually radiate out
towards it and anything outside will gradually
spin in towards it. If I put a variety of starting
conditions in our phase space we see they all arc and
gradually will form back towards this stable
loop. So like I said that's called a limit cycle
and it's really important in things like engineering
where you want some behavior to be guaranteed
to settle back into but in our context of analyzing history
I think it works really well. The idea is that there's
this general rise and fall of things that you can predict
but you're not always going to know it for sure. If there's
some slight variation to all these numbers it
can get back on track. The loop might be
slightly smaller or slightly larger but it'll eventually
stabilize back to the same thing. And we can show
that by adding some random jiggle to one of
our variables and see that we get these kind of
intermediately sized loops which I think look pretty
cool. The general pattern we can see from this
that then Turchin expounds a lot on in his books
is that we start in a position here where all
three values are really low and then the commoner
population starts rising at exponentially which
after a delay will cause the elite population and the
state finances to also increase. But eventually because those are increasing
the tax burden on the commoners is going to go up whether
directly through the state or indirectly through the
elites grabbing more and more of the commoner
surplus. This will eventually cause the commoner
population to slow down and then start sharply declining
which will lead to the elites being able to
take less resources from themselves and then the state to be able
to take less resources from those elites. This period where there are
too many elites but not enough for resources for them
to grab is called elite overproduction by
Turchin and is a big thing he tries to track over
history whether through things like actual
conflict between elites or things like how competitive
is it to get high-level government positions or
university professorships or things like that. This
large amount of elites fighting over a smaller
and smaller pie is going to put a lot of pressure
on the state which as we established in this
model is responsible for somehow alleviating
this pressure. Eventually the state is
going to go bankrupt which causes the
elite population to go down. Again either through either through
fighting each other and wiping each other out, or through a lack of viable
positions that they can fill. Eventually the state collapse leads to
a collapse in elite numbers which leads to less repression on the
common population which leads them to start
increasing their numbers again resetting the whole cycle. And that's at a very high level what Turchin argues is
these 'secular cycles' in history. He does a bunch of
analysis and proposes how long this whole cycle
takes quote unquote "by default" but as we saw
because it's a limit cycle the idea is that if any of
these variables change because of like war or
famine or something not in this model it'll
stabilize back to it. The whole cycle will still
happen but it might be shorter or longer than
the default length. Now I really made this video
because I just think it's cool how closely the math
can track this overall more narrative description of
how things are happening. Whether or not any
of this is accurate is very much not a thing
I'm super qualified in. Even at a really high
level you can pretty easily consider ways in which
different societies should work differently than
this. Like how are the resources going from
normal people to elites to the state feels like a
thing that's going to be different from country
to country. If you kind of go in a Marxian direction
you have different like modes of production
which would tie into that. And also this division
between commoners and elites to me feels like
somewhat arbitrary. Like it makes the math work but like I don't
see any reason you should split it into two groups specifically.
Conceptually you can do stuff like split this
up by regions of space. I could apply it to this
world model that I've been building in other videos or you could
break it up into more like social classes or time periods
or things like that. But as you increase the
number of variables like this eventually you're going
to stop being able to analyze it in the same way.
Because as we increase the social classes from
1 to 2 to 10 to a million to an infinite number
of divisions then at that point you're not dealing
with quote-unquote ordinary differential
equations which is what all of the math we've been
doing has been. And now you're dealing with partial
differential equations which is a whole related but
other field of math. And a lot of the ways we've
been talking about to analyze this stuff like phase
space doesn't work on partial differential
equations. This is getting more into stuff like
simulating liquids and other big fields of data and is
actually more complicated then that because unlike
liquids we have a bunch of these funky non-linearities
and exponential growths. So you can't use a
lot of the tools that exist for analyzing other
partial differential equations. There's also just a
bunch of variables slash parameters in the math
that we're just kind of making up. Like you saw how
arbitrarily I changed it from four resources to
a pop to 15. I kind of just messed around with numbers
until things looked good. And so reasonably in Turchin's books he
spends a lot of time trying to justify what numbers he's picking for
these kind of things and how he's arriving
at those numbers. If what I'm doing feels
arbitrary you should just read his words and not the
summary you're getting from me. An interesting note
about this kind of thing is talking about how can we tell what the
quote-unquote proper number of variables we need to model something
is. So like we saw with the initial elite model
we had adding another dimension didn't really
make the simulation more complicated but there
are properties that can only exist in certain dimensions.
Like we talked about you can't curve back on
yourself in one dimension. There's also a whole
part of chaos theory which is this idea that you can't
have a chaotic system unless you have at
least three variables. The YouTuber Not David
has a cool video about this where you can use something
called shadow manifolds to just look at one variable
and see how it's changing. And use that to determine
the minimum number of dimensions that the
underlying system has to have. And doing the research
for this video actually made me understand
that more because he has a whole comment about
how it doesn't work if the lines ever cross and
he's talking about how in phase space lines can't
cross and I didn't realize that was what was going
on in that video but anyways it's a good video you
should check it out. This video's book recommendation
is Nonlinear Dynamics and Chaos by Steven
Srogatz which is literally a math textbook but for me was a
pretty entertaining read still. Srogatz does a great
job at giving a lot of interesting examples
and saying stuff like oh here's the math and
that's pretty unintuitive so let's look at a diagram
instead which at least I found a lot more helpful
than when I learned about this stuff in a university
course. If you're the type of person who
learns better from lectures than from reading through
a book you can check out Dr. Shane Ross's full
online course that goes through this book on
YouTube. I'll link that in the video description
here. If you're surprised that this YouTube channel
which started with me talking about anime
is now just me lecturing about calculus I'm also
surprised so here we are. This whole video actually
started as a footnote in the script to the last
world building video where I just had one line in
the outline that said oh it's interesting that
structural demographic theory is a limit cycle
and that was it and you know that's turned into
this 35 minute long video or whatever but genuinely
the channel is called fractal philosophy out of
that idea. Philosophy being the love of knowledge and
fractals being something that the more you zoom in
the more detailed they get. So the idea being you
learn a thing and then you learn some new questions
that are interesting and then you look into
those and that causes new questions etc etc. And
actually this is like the two-year anniversary of
this YouTube channel so let me know if you've
been watching since earlier. I genuinely would be
interested to know if like people came for the anime
stuff or the video game videos and are still
interested in this stuff like obviously I'm interested
in all these things but I'm not sure how much audience
retention there is or if there's a big split between people
who watch my technical videos and my less technical
video essay kind of videos. I don't know let me know.
I'd be genuinely interested. The next video on this channel is similarly
a result of me rabbit holing from one line on a previous video
so it's going to be about the connection between
stories and games and I think that'll be interesting.
Next technical video is going to be about
a variant of rock paper scissors that I'm super
excited about but like I'm not sure how much I
can convince other people that it's interesting
but like I find it so cool. So I'm excited about that
video. And then there's another AI video in the
works that's a little more talking about like
art and philosophy. There's a poll to decide
whether to do that one or the game video first and the poll
was very unhelpful so thanks guys. But the real deciding factor is I wanted
to reference a line that's in the new Chainsaw Man movie
and that movie's currently only in theaters so I can't really do that
successfully until it's streaming or on blu-ray or something.
Also there's currently no shortage of video essays
on AI so I figure spending a couple months thinking
about it and letting those ideas marinate a bit
is probably beneficial. But yeah thanks for being
around. Year one of this channel was basically me talking to myself
and year two has been really exciting. We're always learning new
stuff. Obviously we're trying video sponsorships
this video. This is also a much more technical
video than I normally do so we'll see if I'm able
to convey ideas like that well or not. Also
like what I'm doing now. This is a new
thing. Is this weird? Should this be a separate
video? This is more vloggy style? Should this be on a separate
channel? I don't know. We're trying things out. Anyways thanks
for watching this far into the video. Thanks to the patrons
for helping fund this stuff. I'll be back with
more stuff next year.

---
