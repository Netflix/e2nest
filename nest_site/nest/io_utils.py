class ExperimentConfigFileUtils(object):

    @staticmethod
    def add_to_stimulusvotegroup_dict(stimulus_ids, d_stimulusvotegroups):
        # Note: since sg-to-svg is one-to-many, each svg corresponds to a
        # unique sg. Thus, we cannot reuse svg across different sgs, and
        # must create fresh svg_id every time.
        stimulusvotegroup_id = len(d_stimulusvotegroups)
        d_stimulusvotegroups[stimulusvotegroup_id] = {
            'stimulus_ids': stimulus_ids,
            'stimulusvotegroup_id': stimulusvotegroup_id}
        return stimulusvotegroup_id

    @staticmethod
    def add_to_stimulus_dict(filepath, content_id, d_stimuli):
        if filepath in d_stimuli:
            stimulus_id = d_stimuli[filepath]['stimulus_id']
        else:
            stimulus_id = len(d_stimuli)
            d_stimuli[filepath] = {
                'path': filepath,
                'stimulus_id': stimulus_id,
                'type': 'video/mp4',
                'content_id': content_id}
        return stimulus_id

    @staticmethod
    def add_to_content_dict(content_name, d_contents):
        if content_name in d_contents:
            content_id = d_contents[content_name]['content_id']
        else:
            content_id = len(d_contents)
        d_contents[content_name] = {
            'content_id': content_id,
            'name': content_name}
        return content_id

    @staticmethod
    def add_to_stimulusgroup_dict(stimulusvotegroup_ids, d_stimulusgroups):
        if str(stimulusvotegroup_ids) in d_stimulusgroups:
            stimulusgroup_id = d_stimulusgroups[str(stimulusvotegroup_ids)][
                'stimulusgroup_id']
        else:
            stimulusgroup_id = len(d_stimulusgroups)
            d_stimulusgroups[str(stimulusvotegroup_ids)] = {
                'stimulusvotegroup_ids': stimulusvotegroup_ids,
                'stimulusgroup_id': stimulusgroup_id}
        return stimulusgroup_id

    @staticmethod
    def populate_prioritized_etc(stimulusgroup_id, mode, prioritized,
                                 blocklist_stimulusgroup_ids, training_round_ids):
        if mode == 'training':
            round_id = len(prioritized)
            prioritized.append({
                'session_idx': None,
                'round_id': round_id,
                'stimulusgroup_id': stimulusgroup_id,
            })
            blocklist_stimulusgroup_ids.append(stimulusgroup_id)
            training_round_ids.append(round_id)
        elif mode == 'reliability':
            prioritized.append({
                'session_idx': None,
                'round_id': None,
                'stimulusgroup_id': stimulusgroup_id,
            })
            blocklist_stimulusgroup_ids.append(stimulusgroup_id)
        elif mode == 'testing':
            pass  # do nothing
        else:
            assert False
