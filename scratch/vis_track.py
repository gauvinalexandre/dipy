from eztrack import EZTrackingInterface
from traitsui.api import Item, Group, View, ArrayEditor
from traits.api import File, on_trait_change
import nibabel as nib
from nibabel.trackvis import write, empty_header
import numpy as np
from os import path
from dipy.io.bvectxt import read_bvec_file, orientation_to_string, \
                            reorient_bvec
import pickle

class VizTrackingInterface(EZTrackingInterface):

    save_streamlines_to = File('')
    save_counts_to = File('*.nii.gz')

    @on_trait_change('save_streamlines_to')
    def update_save_file(self):
        if self.save_counts_to == '':
            base, ext = path.splitext(self.save_streamlines_to)
            self.save_counts_to = base + '.nii.gz'

    trait_view = View(Group(Group(
                                  Item( 'dwi_images' ),
                                  Item( 'all_inputs' ),
                                  Item( 'min_signal' ),
                                  Item( 'seed_roi' ),
                                  Item( 'seed_density', editor=ArrayEditor() ),
                                  show_border=True),
                            Group(
                                  Item( 'smoothing_kernel_type' ),
                                  Item( 'smoothing_kernel' ),
                                  show_border=True),
                            Group(
                                  Item( 'interpolator' ),
                                  Item( 'model_type' ),
                                  Item( 'sh_order' ),
                                  Item( 'Lambda' ),
                                  Item( 'sphere_coverage' ),
                                  Item( 'min_peak_spacing' ),
                                  Item( 'min_relative_peak' ),
                                  show_border=True),
                            Group(
                                  Item( 'probabilistic' ),
                                  show_border=True),
                            Group(
                                  #Item( 'integrator' ),
                                  Item( 'direction', editor=ArrayEditor() ),
                                  Item( 'track_two_directions'),
                                  Item( 'fa_threshold' ),
                                  Item( 'max_turn_angle' ),
                                  show_border=True),
                            Group(
                                  Item( 'targets' ),
                                  show_border=True),
                            Group(
                                  Item( 'save_streamlines_to' ),
                                  Item( 'save_counts_to' ),
                                  show_border=True),
                            orientation = 'vertical'),
                        buttons=['OK', 'Cancel'], resizable=True)

    def save_streamlines(self, streamlines):
        if self.save_streamlines_to == '':
            return
        trk_hdr = empty_header()
        voxel_order = orientation_to_string(nib.io_orientation(self.affine))
        trk_hdr['voxel_order'] = voxel_order
        trk_hdr['voxel_size'] = self.voxel_size
        trk_hdr['dim'] = self.shape
        trk_tracks = ((ii,None,None) for ii in streamlines)
        write(self.save_streamlines_to, trk_tracks, trk_hdr)
        pickle.dump(self, open(self.save_streamlines_to + '.p', 'wb'))

    def save_counts(self, streamlines):
        if self.save_counts_to == '':
            return
        counts = streamline_counts(streamlines, self.shape, self.voxel_size)
        if counts.max() < 2**16:
            counts = counts.astype('uint16')
        nib.save(nib.Nifti1Image(counts, self.affine), self.save_counts_to)

    def gui_track(self):
        if self.save_streamlines_to == '' and self.save_counts_to == '':
            raiseIOError('must provide filename where to save results')
        streamlines = list(self.track_shm())
        self.save_streamlines(streamlines)
        self.save_counts(streamlines)

if __name__ == "__main__":
    b = VizTrackingInterface()
    b.model_type = 'QballOdf'
    b.min_peak_spacing = np.sqrt(.5)
    b.min_relative_peak = .25
    b.direction = [0,-1,0]
    b.fa_threshold = .150
    b.max_turn_angle = 60
    b.dwi_images = '/home/npapinu/August2011/Jam_5/090529_8597/data.nii.gz'
    b.all_inputs.bvec_file = '/home/npapinu/August2011/Jam_5/090529_8597/qBall/data.bvec'
    b.all_inputs.fa_file = '/home/npapinu/August2011/Jam_5/090529_8597/dti_FA.nii.gz'
    b.all_inputs.bvec_orientation = 'las'
    b.smoothing_kernel_type = 'Box'
    b.smoothing_kernel.shape = (3,3,3)
    b.sh_order = 4
    b.sphere_coverage = 5
    b.Lambda = 0
    b.seed_roi = '/home/npapinu/August2011/Jam_5/090529_8597/qBall/Pole_L_toFA_mask.nii.gz'
    #b.targets.append('/home/bagrata/scrap/target_roi.nii.gz')
    b.probabilistic = False

    b.seed_density = [2,2,2]
    b.save_streamlines_to = '/home/npapinu/August2011/Jam_5/090529_8597/tracks.trk'
    b.save_counts_to = '/home/npapinu/August2011/Jam_5/090529_8597/tracks.nii.gz'
    if b.configure_traits():
        stream = b.gui_track()

