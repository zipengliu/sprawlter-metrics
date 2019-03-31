# coding: utf-8

from sa_metrics import run_store_print
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--data_dir', required=True)
parser.add_argument('--output_dir', required=True)
parser.add_argument('--alpha_nn', default=0.2, type=float)
parser.add_argument('--alpha_ne', default=0.2, type=float)
parser.add_argument('--alpha_ee', default=0.2, type=float)
parser.add_argument('--ee', choices=['linear', 'quadratic'], default='linear')
parser.add_argument('--skip_nn_computation', default=False, action='store_true')
parser.add_argument('--skip_ne_computation', default=False, action='store_true')
parser.add_argument('--skip_ee_computation', default=False, action='store_true')
parser.add_argument('--skip_SA_metrics', default=False, action='store_true')
parser.add_argument('--skip_Dunne_metrics', default=False, action='store_true')
parser.add_argument('--skip_level_breakdown', default=False, action='store_true')
parser.add_argument('--debug', default=False, action='store_true')

args = parser.parse_args()
print(args)

files = [
         'four-clusters-original',
         'four-clusters-ne0',
         'four-clusters-ne1',
         'four-clusters-nn0',
         'four-clusters-nn1',
         'four-clusters-nn2',
         'four-clusters-nn3',
         'four-clusters-nn4',
         'four-clusters-sprawl',
         'four-clusters-ee0',
         'four-clusters-ee-glancing',
         
         'special-cases-1',
         'special-cases-2',
         'special-cases-3',
         'special-cases-4',
         'special-cases-5',
         'special-cases-6',
         'special-cases-7',
    
         'progression-nn-none',
         'progression-nn-touch-leaf',
         'progression-nn-touch-meta',
         'progression-nn-some-leaf',
         'progression-nn-some-meta',
         'progression-nn-near-max-leaf',
         'progression-nn-near-max-meta',
    
         'progression-ne-touch-leaf',        
         'progression-ne-touch-meta',
         'progression-ne-some-leaf',
         'progression-ne-some-meta',      
         'progression-ne-near-max-leaf',
         'progression-ne-near-max-meta',
    
         'progression-ee-ortho',
         'progression-ee-half',
         'progression-ee-near-glancing',
         'progression-ee-glancing',
         
         # 'midsize-handmade1-1',
         # 'midsize-handmade1-100',
         
         'coauthor-main-comp-gem',
         'coauthor-main-comp-grouseflocks-0',
         'coauthor-main-comp-grouseflocks-1',
         'coauthor-main-comp-grouseflocks-2',
         'coauthor-main-comp-koala',

         'grouseflocks-ivOrigins-gem',
         'grouseflocks-ivOrigins-grouseflocks-open-2',
         'grouseflocks-ivOrigins-grouseflocks-open-4',
         'grouseflocks-ivOrigins-koala',
         #'grouseflocks-moviedb-rateonly-gem',
         # 'grouseflocks-moviedb-rateonly-grouseflocks-1',
         # 'grouseflocks-moviedb-rateonly-grouseflocks-2',
         #'grouseflocks-moviedb-rateonly-koala',
         #'grouseflocks-moviedb-gem',
         #'grouseflocks-moviedb-koala',

         'partition-add32-fm3',
         'partition-add32-grouseflocks-open-0',
         'partition-add32-grouseflocks-open-1',
         'partition-add32-grouseflocks-open-5',
         'partition-add32-koala',
         #'partition-bcsstk33-grouseflocks-open-3',
         #'partition-bcsstk33-grouseflocks-open-8',
         #'partition-bcsstk33-fm3',
         #'partition-bcsstk33-koala,
         
         'snap-email-eu-core-main-comp-gem',
#          'snap-email-eu-core-main-comp-grouseflocks-open-4',
         'snap-email-eu-core-main-comp-grouseflocks-1',
         'snap-email-eu-core-main-comp-grouseflocks-2',
         'snap-email-eu-core-main-comp-koala'
]

# FOR TESTING
# files = [
#         'snap-email-eu-core-main-comp-grouseflocks-1',
#          'snap-email-eu-core-main-comp-grouseflocks-2',
#         'coauthor-main-comp-grouseflocks-0',
#          'coauthor-main-comp-grouseflocks-1',
#          'coauthor-main-comp-grouseflocks-2'
# ]
# files = ['four-clusters-original',
#          'four-clusters-ne0',
#          'four-clusters-ne1',
#          'four-clusters-nn0',
#          'four-clusters-nn1',
#          'four-clusters-nn2',
#          'four-clusters-ee0']


for f in files:
    run_store_print(args.data_dir,
                    f,
                    output_dir=args.output_dir,
                    # area_penalty_func_type='power',
                    # length_penalty_func_type='linear',
                    angle_penalty_func_type=args.ee,
                    alpha_nn=args.alpha_nn,
                    alpha_ne=args.alpha_ne,
                    alpha_ee=args.alpha_ee,
                    skip_nn_computation=args.skip_nn_computation,
                    skip_ne_computation=args.skip_ne_computation,
                    skip_ee_computation=args.skip_ee_computation,
                    skip_SA_metrics=args.skip_SA_metrics,
                    skip_Dunne_metrics=args.skip_Dunne_metrics,
                    skip_level_breakdown=args.skip_level_breakdown,
                    debug=args.debug)

