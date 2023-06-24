# Question Generation from Educational Texts

This is a project I worked on in spring 2023 with 3 teammates. We scraped large amounts of open educational text and processed it to separate the lectures. Each lecture has a corresponding list of questions. I scraped [CK12](https://github.com/timothelaborie/Eduquest/tree/main/scraping/ck12) and [OpenTextBC](https://github.com/timothelaborie/Eduquest/tree/main/scraping/opentextbc), and processed OpenTextBC to remove the noise and issues from it using regular expressions.

I also trained a [LoRA of a Bloom model](https://github.com/timothelaborie/Eduquest/blob/main/question_gen/main.ipynb) to make the model generate new questions.

You can read the research paper [here](https://github.com/timothelaborie/Eduquest/blob/main/paper.pdf)
