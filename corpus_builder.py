import os
import re
import time
import random
import shutil
import progressbar
from lxml import etree
from JobTitleNormalization import normalize_job_titles

user_name = os.environ.get('USER')


def split_data(labels_list):
    """
    Function to split the dataset into training and heldout datasets

    Args:
        labels_list -- list of tuples with filename and tag information for each resume
    """

    # Path where the sample text resumes are present
    source_dir = '/Users/' + user_name + '/Documents/Data/samples_0408_text'

    # Store the training and heldout data in different directories.
    training_dir = '/Users/' + user_name + '/Documents/Data/training_0408'
    heldout_dir = '/Users/' + user_name + '/Documents/Data/heldout_0408'

    random.seed(int(time.time()))
    random.shuffle(labels_list)

    num_files = len(labels_list)

    # Split the training and heldout files
    training_files = labels_list[:int(num_files*0.8)]
    heldout_files = labels_list[int(num_files*0.8) + 1:]

    labels = open('/Users/' + user_name + '/Documents/Data/labels_0408.txt', 'w')
    labels_heldout = open('/Users/' + user_name + '/Documents/Data/labels_heldout_0408.txt', 'w')

    for (filename, tag) in training_files:
        shutil.copy2(source_dir + '/' + filename, training_dir)
        labels.writelines(filename + "\t" + tag + "\n")

    for (filename, tag) in heldout_files:
        shutil.copy2(source_dir + '/' + filename, heldout_dir)
        labels_heldout.writelines(filename + "\t" + tag + "\n")

    labels.close()
    labels_heldout.close()


def stripxml(data):
    """
    Strip the xml tags from the xml to make it plaintext

    Args:
        data -- Resume xml

    Returns:
        text -- plaintext resume without any xml tags.
    """
    pattern = re.compile(r'<.*?>')
    text = pattern.sub('', data)
    return text

   
def prepare_data(source_dir):
    """
    Function to prepare data and split training and test data.

    Args:
        source_dir -- path to the source xml files.

    """

    # Get the files from the source directory
    files = [f for (dirpath, dirnames, filenames) in os.walk(source_dir) for f in filenames if f[-4:] == '.txt']

    names = []
    job_titles = []

    top_jobs = \
        ['consultant', 'director', 'project manager', 'vice president', 'software engineer', 'graphic designer',
         'administrative assistant', 'president', 'senior software engineer', 'accountant', 'web developer',
         'executive assistant', 'senior manager', 'business analyst', 'senior project manager',
         'research assistant', 'program manager', 'accounting manager', 'senior consultant', 'marketing manager',
         'customer service representative', 'staff accountant', 'business development manager', 'general manager',
         'assistant manager', 'office assistant', 'sales representative', 'account executive', 'office manager',
         'senior accountant', 'chief executive officer', 'sales associate', 'marketing director',
         'senior business analyst', 'senior director', 'product manager', 'designer', 'marketing consultant',
         'operations manager', 'analyst'
        ]

    j, bar = 0, pbar(len(files))
    bar.start()
    labels_list = []

    # From each xml file extract the information and store in plaintext files.
    for fname in files:
        # Create an xml parser object
        xml = etree.parse(source_dir + '/' + fname)

        # Extract the current job title, and current job element from xml
        current_job_title = xml.xpath('//job[@end = "present"]/title/text()')
        current_job_title = normalize_job_titles(current_job_title)
        current_job = xml.xpath('//job[@end = "present"]')

        # Extract the contact information from xml.
        contact = xml.xpath('//contact')

        try:
            # Since there are many duplicate resumes in the data, filter out the resumes based on candidate name.
            # Extract the candidate name from the resume
            name = xml.xpath('//givenname/text()')[0] + ' ' + xml.xpath('//surname/text()')[0]

            if name not in names:
                names.append(name)

                # Remove the candidate contact information from the resume.
                if contact:
                        contact[0].getparent().remove(contact[0])

                # Remove the current job section from the resume as we will be using current job title as lable and
                # use our algorithm to predict it.
                if current_job:
                    if len(current_job) > 1:
                        while i < len(current_job):
                            current_job[i].getparent().remove(current_job[i])
                            i += 1
                    else:
                        current_job[0].getparent().remove(current_job[0])

                    # Convert xml to string.
                    xml = etree.tostring(xml, pretty_print=True)

                    # Strip the xml tags from the resume.
                    text_data = stripxml(xml)
                    i = 0
                    flag = 0

                    # From the resume text remove all the words matching the current job title as we do not want any
                    # information about the current job in the resume text.
                    if current_job_title:
                        i = 0
                        if len(current_job_title) > 1:
                            while i < len(current_job_title):
                                text_data = text_data.replace(current_job_title[i].strip(), '')
                                job_titles.append(current_job_title[i].strip())
                                i += 1

                                # Set flag to 1 if the current job title is present in top 20 jobs.
                                if current_job_title[i] in top_jobs:
                                    flag = 1
                        else:
                            text_data = text_data.replace(current_job_title[0].strip(), '')
                            job_titles.append(current_job_title[0].strip())
                            if current_job_title[i] in top_jobs:
                                flag = 1

                # Only save the resumes whose current job title is present in the top 20 jobs
                if flag == 1:

                    if current_job_title:
                        directory = '/Users/' + user_name + '/Documents/Data/samples_0408_text/'
                        f = open(directory + '%s' % fname[:-4] + '_plaintext.txt', 'w')
                        f.write(text_data)
                        f.close()

                        labels_list.append((fname[:-4] + '_plaintext.txt', current_job_title[0].replace('\n', '')))
        except:
            pass

        j += 1
        bar.update(j)
    bar.finish()

    # Split the saved resumes (resumes belonging to top 50 job titles) into training and heldout datasets.
    split_data(labels_list)

    return


def pbar(size):
    """
    Function to display the progress of a long running operation.

    """
    bar = progressbar.ProgressBar(maxval=size,
                                  widgets=[progressbar.Bar('=', '[', ']'),
                                           ' ', progressbar.Percentage(),
                                           ' ', progressbar.ETA(),
                                           ' ', progressbar.Counter(),
                                           '/%s' % size])
    return bar

if __name__ == "__main__":
    prepare_data('/Users/' + user_name + '/Documents/Data/samples_0408')

